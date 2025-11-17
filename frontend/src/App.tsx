import { useState, useEffect } from 'react';
import { TopNavigation } from './components/TopNavigation';
import { ControlPanel } from './components/ControlPanel';
import { Dashboard } from './components/Dashboard';

export type ProcessState = '空闲' | '运行中' | '验证中' | '已完成';

export interface GenerationConfig {
  numSamples: number;
  multiRatio: number;
  toolCount: number;
  toolCountMode: 'single' | 'range';
  toolCountMin: number;
  toolCountMax: number;
  concurrency: number;
  toolListPath: string;
  baseModel: string;
  modelApiUrl: string;
  apiKey: string;
  outputDir: string;
  saveConfig: boolean;
}

export interface GenerationStats {
  progress: number;
  batchCount: number;
  generationRate: number;
  singleTurnCount: number;
  multiTurnCount: number;
  validationSuccessRate: number;
  errors: string[];
}

export default function App() {
  const [processState, setProcessState] = useState<ProcessState>('空闲');
  const [config, setConfig] = useState<GenerationConfig>({
    numSamples: 1000,
    multiRatio: 0.3,
    toolCount: 3,
    toolCountMode: 'single',
    toolCountMin: 2,
    toolCountMax: 5,
    concurrency: 4,
    toolListPath: 'configs/tools_registry.json',
    baseModel: 'deepseek-chat',
    modelApiUrl: 'https://api.deepseek.com/v1',
    apiKey: '',
    outputDir: 'data/processed',
    saveConfig: false,
  });
  const [stats, setStats] = useState<GenerationStats>({
    progress: 0,
    batchCount: 0,
    generationRate: 0,
    singleTurnCount: 0,
    multiTurnCount: 0,
    validationSuccessRate: 100,
    errors: [],
  });
  const [elapsedTime, setElapsedTime] = useState(0);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (processState === '运行中' || processState === '验证中') {
      interval = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [processState]);

  const handleStartGeneration = async () => {
    try {
      // Validate API key
      if (!config.apiKey || config.apiKey.trim() === '') {
        setStats(prev => ({
          ...prev,
          errors: ['错误: 请先填写 API Key。DeepSeek API Key 可从 https://platform.deepseek.com 获取']
        }));
        return;
      }

      setProcessState('运行中');
      setStats({
        progress: 0,
        batchCount: 0,
        generationRate: 0,
        singleTurnCount: 0,
        multiTurnCount: 0,
        validationSuccessRate: 100,
        errors: [],
      });
      setElapsedTime(0);
      setLogs([]);

      // 调用后端API启动生成任务
      const response = await fetch('/api/generate/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_samples: config.numSamples,
          multi_ratio: config.multiRatio,
          tool_count: config.toolCount,
          tool_count_mode: config.toolCountMode,
          tool_count_min: config.toolCountMin,
          tool_count_max: config.toolCountMax,
          concurrency: config.concurrency,
          tool_list_path: config.toolListPath,
          base_model: config.baseModel,
          model_api_url: config.modelApiUrl,
          api_key: config.apiKey,
          output_dir: config.outputDir,
          batch_size: 100,
          strict_validation: false,
          auto_correction: true,
          seed: null,
        }),
      });

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.statusText}`);
      }

      const data = await response.json();
      setCurrentTaskId(data.task_id);

      // 建立WebSocket连接获取实时更新
      const ws = new WebSocket(`ws://localhost:8000/api/logs/${data.task_id}`);

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'stats') {
          const statsData = message.data;
          setStats({
            progress: statsData.progress_percent ?? 0,
            batchCount: Math.floor((statsData.completed_count ?? 0) / 10),
            generationRate: statsData.rate ?? 0,
            singleTurnCount: statsData.single_turn_count ?? 0,
            multiTurnCount: statsData.multi_turn_count ?? 0,
            validationSuccessRate: statsData.validation_success_rate ?? 0,
            errors: statsData.failed_count > 0 ? [`验证失败: ${statsData.failed_count} 个样本`] : [],
          });
        } else if (message.type === 'log') {
          const logData = message.data;

          // Add log to logs array
          setLogs(prev => [...prev, logData].slice(-100)); // Keep last 100 logs

          // Check for authentication errors (更精确的匹配，避免误判"401/500"这样的进度信息)
          if (logData.includes('Authentication Fails') ||
              (logData.includes('401') && (logData.includes('Unauthorized') || logData.includes('认证')))) {
            setProcessState('空闲');
            setStats(prev => ({
              ...prev,
              errors: [...prev.errors, '认证失败: API Key 无效或已过期，请检查 API Key 是否正确']
            }));
            ws.close();
          } else if (logData.includes('任务完成')) {
            setProcessState('已完成');
            ws.close();
          } else if (logData.includes('验证')) {
            setProcessState('验证中');
          } else if (message.level === 'error' || logData.includes('错误') || logData.includes('失败')) {
            // Capture backend errors
            setStats(prev => ({
              ...prev,
              errors: [...prev.errors, logData]
            }));
          }
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        setProcessState('空闲');
        setStats(prev => ({ ...prev, errors: [...prev.errors, 'WebSocket连接失败'] }));
      };

      ws.onclose = () => {
        console.log('WebSocket连接已关闭');
      };

    } catch (error) {
      console.error('启动生成失败:', error);
      setProcessState('空闲');
      setStats(prev => ({
        ...prev,
        errors: [...prev.errors, `错误: ${error instanceof Error ? error.message : '未知错误'}`]
      }));
    }
  };

  const handleDownload = async () => {
    if (!currentTaskId) {
      alert('没有可下载的数据');
      return;
    }

    try {
      const response = await fetch(`/api/download/${currentTaskId}`);

      if (!response.ok) {
        throw new Error('下载失败');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `autotool_dpo_${currentTaskId}.jsonl`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载失败:', error);
      alert('下载失败，请查看控制台');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0e27] via-[#151b3d] to-[#0a0e27] text-slate-200">
      <TopNavigation processState={processState} />
      
      <div className="flex h-[calc(100vh-64px)]">
        <ControlPanel 
          config={config}
          setConfig={setConfig}
          onStartGeneration={handleStartGeneration}
          isRunning={processState === '运行中' || processState === '验证中'}
        />
        
        <Dashboard
          stats={stats}
          onDownload={handleDownload}
          isCompleted={processState === '已完成'}
          logs={logs}
        />
      </div>
    </div>
  );
}
