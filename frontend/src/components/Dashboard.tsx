import { Card } from './ui/card';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Download, TrendingUp, Layers, CheckCircle, BarChart3 } from 'lucide-react';
import type { GenerationStats } from '../App';

interface DashboardProps {
  stats: GenerationStats;
  onDownload: () => void;
  isCompleted: boolean;
  logs?: string[];
}

export function Dashboard({ stats, onDownload, isCompleted, logs = [] }: DashboardProps) {
  return (
    <div className="flex-1 p-6 overflow-y-auto space-y-6">
      {/* Progress Section */}
      <Card className="bg-slate-800/30 border-slate-700/50 p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-slate-100">生成进度</h3>
          <span className="text-2xl text-[#00d9ff]">{stats.progress.toFixed(1)}%</span>
        </div>
        {/* 霓虹蓝进度条 */}
        <div className="relative h-3 w-full overflow-hidden rounded-full bg-slate-700/50">
          <div
            className="h-full bg-gradient-to-r from-[#00d9ff] to-[#00a8cc] transition-all duration-300 shadow-[0_0_10px_rgba(0,217,255,0.5)]"
            style={{ width: `${stats.progress}%` }}
          />
        </div>
        <div className="mt-3 flex items-center justify-between text-sm text-slate-400">
          <span>批次 {stats.batchCount} 处理中...</span>
          <span>{stats.progress === 100 ? '已完成' : '进行中'}</span>
        </div>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-slate-800/40 to-slate-800/20 border-slate-700/50 p-4 backdrop-blur-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-slate-400 mb-1">生成速率</p>
              <p className="text-2xl text-slate-100">{stats.generationRate.toFixed(2)}</p>
              <p className="text-xs text-slate-500 mt-1">样本/秒</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-[#00d9ff]/10 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-[#00d9ff]" />
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/40 to-slate-800/20 border-slate-700/50 p-4 backdrop-blur-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-slate-400 mb-1">对话类型分布</p>
              <p className="text-2xl text-slate-100">{stats.singleTurnCount}/{stats.multiTurnCount}</p>
              <p className="text-xs text-slate-500 mt-1">单轮 / 多轮</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Layers className="w-5 h-5 text-purple-400" />
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/40 to-slate-800/20 border-slate-700/50 p-4 backdrop-blur-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-slate-400 mb-1">验证成功率</p>
              <p className="text-2xl text-slate-100">{stats.validationSuccessRate.toFixed(1)}%</p>
              <p className="text-xs text-slate-500 mt-1">通过率</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
          </div>
        </Card>
      </div>

      {/* Log Console */}
      <Card className="bg-slate-800/30 border-slate-700/50 backdrop-blur-sm">
        <div className="border-b border-slate-700/50 p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-[#00d9ff]" />
            <h3 className="text-slate-100">实时日志</h3>
          </div>
          <div className="flex gap-2">
            <div className={`w-2 h-2 rounded-full ${logs.length > 0 ? 'bg-green-400 animate-pulse' : 'bg-slate-600'}`} />
            <span className="text-xs text-slate-400">{logs.length > 0 ? '活跃' : '等待'}</span>
          </div>
        </div>
        <ScrollArea className="h-64 p-4">
          <div className="space-y-2 font-mono text-xs">
            {logs.length > 0 ? (
              logs.map((log, index) => {
                // Parse log level and content
                let levelColor = 'text-slate-400';
                let levelText = '[信息]';

                if (log.includes('成功') || log.includes('完成') || log.includes('SUCCESS')) {
                  levelColor = 'text-green-400';
                  levelText = '[成功]';
                } else if (log.includes('错误') || log.includes('失败') || log.includes('ERROR')) {
                  levelColor = 'text-red-400';
                  levelText = '[错误]';
                } else if (log.includes('警告') || log.includes('WARNING')) {
                  levelColor = 'text-yellow-400';
                  levelText = '[警告]';
                } else if (log.includes('开始') || log.includes('启动')) {
                  levelColor = 'text-[#00d9ff]';
                  levelText = '[信息]';
                }

                return (
                  <div key={index} className="text-slate-400">
                    <span className={levelColor}>{levelText}</span> {log}
                  </div>
                );
              })
            ) : (
              <div className="text-slate-500">等待生成开始...</div>
            )}
            {stats.errors.map((error, i) => (
              <div key={`error-${i}`} className="text-yellow-400">
                <span className="text-yellow-400">[警告]</span> {error}
              </div>
            ))}
          </div>
        </ScrollArea>
      </Card>

      {/* Download Button */}
      <Button
        onClick={onDownload}
        disabled={!isCompleted}
        className="w-full h-12 bg-slate-700/50 hover:bg-slate-700 text-slate-100 border border-slate-600 hover:border-[#00d9ff] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Download className="w-5 h-5 mr-2" />
        下载数据集 (JSONL)
      </Button>
    </div>
  );
}
