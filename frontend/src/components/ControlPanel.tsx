import { useState } from 'react';
import { Card } from './ui/card';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Switch } from './ui/switch';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Play, Settings2, Save, Eye, ChevronDown, Check } from 'lucide-react';
import type { GenerationConfig } from '../App';

interface ControlPanelProps {
  config: GenerationConfig;
  setConfig: (config: GenerationConfig) => void;
  onStartGeneration: () => void;
  isRunning: boolean;
}

export function ControlPanel({ config, setConfig, onStartGeneration, isRunning }: ControlPanelProps) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [modelPopoverOpen, setModelPopoverOpen] = useState(false);
  const [modelInputValue, setModelInputValue] = useState(config.baseModel);
  const [showAllModels, setShowAllModels] = useState(false);

  const modelOptions = [
    { value: 'deepseek-chat', label: 'DeepSeek Chat' },
    { value: 'qwen-turbo', label: 'Qwen Turbo' },
    { value: 'qwen-plus', label: 'Qwen Plus' },
    { value: 'qwen-max', label: 'Qwen Max' },
    { value: 'glm-4', label: 'GLM-4' },
    { value: 'moonshot-v1-8k', label: 'Moonshot V1 8K' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'claude-3-opus', label: 'Claude 3 Opus' },
    { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
  ];

  const filteredModels = (showAllModels || !modelInputValue)
    ? modelOptions
    : modelOptions.filter(option =>
        option.value.toLowerCase().includes(modelInputValue.toLowerCase()) ||
        option.label.toLowerCase().includes(modelInputValue.toLowerCase())
      );

  const handlePreview = async () => {
    try {
      const url = `/api/tools/preview?path=${encodeURIComponent(config.toolListPath)}`;
      const response = await fetch(url);

      if (response.ok) {
        const text = await response.text();
        setPreviewContent(text);
        setPreviewOpen(true);
      } else {
        const errorText = await response.text();
        setPreviewContent(`无法加载工具配置\n\n错误: ${errorText}\n\n请确保:\n1. 路径正确: ${config.toolListPath}\n2. 后端服务已启动\n3. 文件存在且格式正确`);
        setPreviewOpen(true);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      setPreviewContent(`加载失败\n\n错误: ${errorMessage}\n\n请确保:\n1. 后端服务已启动\n2. 路径正确: ${config.toolListPath}\n3. 文件存在且可访问`);
      setPreviewOpen(true);
    }
  };

  return (
    <div className="w-[30%] border-r border-slate-700/50 bg-[#0f172a]/40 p-4 overflow-y-auto">
      <div className="flex items-center gap-2 mb-4">
        <Settings2 className="w-5 h-5 text-[#00d9ff]" />
        <h2 className="text-slate-100">生成参数</h2>
      </div>

      <div className="space-y-3">
        <Card className="bg-slate-800/50 border-slate-700/50 p-3 backdrop-blur-sm">
          <div className="space-y-2.5">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label htmlFor="numSamples" className="text-slate-300 mb-1 block text-sm">
                  样本数量
                </Label>
                <Input
                  id="numSamples"
                  type="number"
                  value={config.numSamples}
                  onChange={(e) => setConfig({ ...config, numSamples: parseInt(e.target.value) || 0 })}
                  className="bg-slate-900/50 border-slate-600 text-slate-100 focus:border-[#00d9ff] focus:ring-[#00d9ff]/30 h-9"
                  disabled={isRunning}
                />
              </div>
              <div>
                <Label htmlFor="concurrency" className="text-slate-300 mb-1 block text-sm">
                  并发级别
                </Label>
                <Input
                  id="concurrency"
                  type="number"
                  value={config.concurrency}
                  onChange={(e) => setConfig({ ...config, concurrency: parseInt(e.target.value) || 0 })}
                  className="bg-slate-900/50 border-slate-600 text-slate-100 focus:border-[#00d9ff] focus:ring-[#00d9ff]/30 h-9"
                  disabled={isRunning}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="multiRatio" className="text-slate-300 mb-1.5 block text-sm">
                多轮对话比例: {(config.multiRatio * 100).toFixed(0)}%
              </Label>
              <div className="relative pb-0.5">
                <input
                  type="range"
                  id="multiRatio"
                  min="0"
                  max="100"
                  step="5"
                  value={config.multiRatio * 100}
                  onChange={(e) => setConfig({ ...config, multiRatio: parseInt(e.target.value) / 100 })}
                  disabled={isRunning}
                  className="w-full h-2 bg-slate-700/50 rounded-lg appearance-none cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none
                    [&::-webkit-slider-thumb]:w-4
                    [&::-webkit-slider-thumb]:h-4
                    [&::-webkit-slider-thumb]:rounded-full
                    [&::-webkit-slider-thumb]:bg-gradient-to-r
                    [&::-webkit-slider-thumb]:from-[#00d9ff]
                    [&::-webkit-slider-thumb]:to-[#0066ff]
                    [&::-webkit-slider-thumb]:shadow-[0_0_10px_rgba(0,217,255,0.6)]
                    [&::-webkit-slider-thumb]:cursor-pointer
                    [&::-webkit-slider-thumb]:transition-all
                    [&::-webkit-slider-thumb]:hover:shadow-[0_0_15px_rgba(0,217,255,0.8)]
                    [&::-webkit-slider-thumb]:hover:scale-110
                    [&::-moz-range-thumb]:w-4
                    [&::-moz-range-thumb]:h-4
                    [&::-moz-range-thumb]:rounded-full
                    [&::-moz-range-thumb]:bg-gradient-to-r
                    [&::-moz-range-thumb]:from-[#00d9ff]
                    [&::-moz-range-thumb]:to-[#0066ff]
                    [&::-moz-range-thumb]:shadow-[0_0_10px_rgba(0,217,255,0.6)]
                    [&::-moz-range-thumb]:border-0
                    [&::-moz-range-thumb]:cursor-pointer
                    [&::-moz-range-thumb]:transition-all
                    [&::-moz-range-thumb]:hover:shadow-[0_0_15px_rgba(0,217,255,0.8)]
                    [&::-moz-range-thumb]:hover:scale-110
                    disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{
                    background: `linear-gradient(to right, #00d9ff ${config.multiRatio * 100}%, rgb(51 65 85 / 0.5) ${config.multiRatio * 100}%)`
                  }}
                />
              </div>
            </div>

            <div>
              <Label className="text-slate-300 mb-1.5 block text-sm">
                工具数配置
              </Label>
              <RadioGroup
                value={config.toolCountMode}
                onValueChange={(value: 'single' | 'range') => setConfig({ ...config, toolCountMode: value })}
                className="flex gap-4 mb-2"
                disabled={isRunning}
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="single" id="single" className="border-slate-600 text-[#00d9ff]" />
                  <Label htmlFor="single" className="text-slate-300 text-sm cursor-pointer">单值</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="range" id="range" className="border-slate-600 text-[#00d9ff]" />
                  <Label htmlFor="range" className="text-slate-300 text-sm cursor-pointer">范围</Label>
                </div>
              </RadioGroup>
              
              {config.toolCountMode === 'single' ? (
                <Input
                  id="toolCount"
                  type="number"
                  value={config.toolCount}
                  onChange={(e) => setConfig({ ...config, toolCount: parseInt(e.target.value) || 0 })}
                  className="bg-slate-900/50 border-slate-600 text-slate-100 focus:border-[#00d9ff] focus:ring-[#00d9ff]/30 h-9"
                  disabled={isRunning}
                  placeholder="固定工具数"
                />
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    value={config.toolCountMin}
                    onChange={(e) => setConfig({ ...config, toolCountMin: parseInt(e.target.value) || 0 })}
                    className="bg-slate-900/50 border-slate-600 text-slate-100 focus:border-[#00d9ff] focus:ring-[#00d9ff]/30 h-9"
                    disabled={isRunning}
                    placeholder="最小值"
                  />
                  <Input
                    type="number"
                    value={config.toolCountMax}
                    onChange={(e) => setConfig({ ...config, toolCountMax: parseInt(e.target.value) || 0 })}
                    className="bg-slate-900/50 border-slate-600 text-slate-100 focus:border-[#00d9ff] focus:ring-[#00d9ff]/30 h-9"
                    disabled={isRunning}
                    placeholder="最大值"
                  />
                </div>
              )}
            </div>

            <div>
              <Label htmlFor="toolListPath" className="text-slate-300 mb-1 block text-sm">
                工具列表路径
              </Label>
              <div className="flex gap-2">
                <Input
                  id="toolListPath"
                  type="text"
                  value={config.toolListPath}
                  onChange={(e) => setConfig({ ...config, toolListPath: e.target.value })}
                  className="bg-slate-900/50 border-slate-600 text-slate-100 focus:border-[#00d9ff] focus:ring-[#00d9ff]/30 font-mono text-sm h-9 flex-1"
                  disabled={isRunning}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handlePreview}
                  className="h-9 px-3 bg-slate-900/50 border border-slate-600/60 text-slate-300 hover:bg-slate-800/70 hover:text-[#00d9ff] hover:border-[#00d9ff]/40 hover:shadow-[0_0_8px_rgba(0,217,255,0.15)] transition-all duration-200 disabled:opacity-50"
                  disabled={isRunning}
                >
                  <Eye className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700/50 p-3 backdrop-blur-sm">
          <div className="space-y-2.5">
            <div>
              <Label htmlFor="baseModel" className="text-slate-300 mb-1 block text-sm">
                基础模型
              </Label>
              <Popover open={modelPopoverOpen} onOpenChange={setModelPopoverOpen}>
                <PopoverTrigger asChild>
                  <div className="relative">
                    <Input
                      id="baseModel"
                      type="text"
                      value={modelInputValue}
                      onChange={(e) => {
                        setModelInputValue(e.target.value);
                        setConfig({ ...config, baseModel: e.target.value });
                        setShowAllModels(false);
                      }}
                      onClick={() => {
                        if (!modelInputValue.trim()) {
                          setShowAllModels(true);
                          setModelPopoverOpen(true);
                        }
                      }}
                      className="bg-slate-900/50 border-slate-600 text-slate-100 focus:border-[#00d9ff] focus:ring-[#00d9ff]/30 font-mono text-sm h-9 pr-9"
                      disabled={isRunning}
                      placeholder="选择或输入模型名称"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        setShowAllModels(true);
                        setModelPopoverOpen(!modelPopoverOpen);
                      }}
                      disabled={isRunning}
                      className="absolute right-0 top-0 h-full px-3 flex items-center hover:bg-slate-800/50 rounded-r transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${modelPopoverOpen ? 'rotate-180 text-[#00d9ff]' : ''}`} />
                    </button>
                  </div>
                </PopoverTrigger>
                <PopoverContent 
                  className="w-[var(--radix-popover-trigger-width)] p-0 bg-slate-900/95 border-slate-700/50 shadow-[0_0_20px_rgba(0,217,255,0.1)] backdrop-blur-xl"
                  align="start"
                  sideOffset={4}
                >
                  <div className="max-h-[240px] overflow-y-auto">
                    {filteredModels.length > 0 ? (
                      filteredModels.map((option) => (
                        <button
                          key={option.value}
                          onClick={() => {
                            setModelInputValue(option.value);
                            setConfig({ ...config, baseModel: option.value });
                            setModelPopoverOpen(false);
                          }}
                          className="w-full text-left px-3.5 py-2 hover:bg-gradient-to-r hover:from-slate-800/60 hover:to-slate-800/40 text-slate-300 hover:text-[#00d9ff] transition-all duration-200 flex items-center justify-between group relative overflow-hidden"
                        >
                          <span className="font-mono text-sm tracking-wide relative z-10">{option.value}</span>
                          {config.baseModel === option.value && (
                            <Check className="w-3.5 h-3.5 text-[#00d9ff] relative z-10 drop-shadow-[0_0_4px_rgba(0,217,255,0.5)]" />
                          )}
                          <div className="absolute inset-0 bg-gradient-to-r from-[#00d9ff]/0 via-[#00d9ff]/5 to-[#00d9ff]/0 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                        </button>
                      ))
                    ) : (
                      <div className="px-3.5 py-6 text-center text-sm text-slate-500/80">
                        未找到匹配的模型
                      </div>
                    )}
                  </div>
                </PopoverContent>
              </Popover>
            </div>

            <div>
              <Label htmlFor="modelApiUrl" className="text-slate-300 mb-1 block text-sm">
                API 地址
              </Label>
              <Input
                id="modelApiUrl"
                type="text"
                value={config.modelApiUrl}
                onChange={(e) => setConfig({ ...config, modelApiUrl: e.target.value })}
                className="bg-slate-900/50 border-slate-600 text-slate-100 focus:border-[#00d9ff] focus:ring-[#00d9ff]/30 font-mono text-sm h-9"
                disabled={isRunning}
                placeholder="https://api.openai.com/v1"
              />
            </div>

            <div>
              <Label htmlFor="apiKey" className="text-slate-300 mb-1 block text-sm">
                API Key
              </Label>
              <Input
                id="apiKey"
                type="password"
                value={config.apiKey}
                onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                className="bg-slate-900/50 border-slate-600 text-slate-100 focus:border-[#00d9ff] focus:ring-[#00d9ff]/30 font-mono text-sm h-9"
                disabled={isRunning}
                placeholder="sk-..."
              />
            </div>

            <div>
              <Label htmlFor="outputDir" className="text-slate-300 mb-1 block text-sm">
                输出目录
              </Label>
              <Input
                id="outputDir"
                type="text"
                value={config.outputDir}
                onChange={(e) => setConfig({ ...config, outputDir: e.target.value })}
                className="bg-slate-900/50 border-slate-600 text-slate-100 focus:border-[#00d9ff] focus:ring-[#00d9ff]/30 font-mono text-sm h-9"
                disabled={isRunning}
              />
            </div>
          </div>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700/50 p-2.5 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Save className="w-3.5 h-3.5 text-[#00d9ff]" />
              <Label htmlFor="saveConfig" className="text-slate-300 cursor-pointer text-sm">
                保存配置
              </Label>
            </div>
            <Switch
              id="saveConfig"
              checked={config.saveConfig}
              onCheckedChange={(checked) => setConfig({ ...config, saveConfig: checked })}
              disabled={isRunning}
              className="data-[state=checked]:bg-[#00d9ff]"
            />
          </div>
        </Card>

        <Button
          onClick={onStartGeneration}
          disabled={isRunning}
          className="w-full h-10 bg-gradient-to-r from-[#00d9ff] to-[#0066ff] hover:from-[#00c4ea] hover:to-[#0055ee] text-slate-900 shadow-[0_0_20px_rgba(0,217,255,0.5)] hover:shadow-[0_0_30px_rgba(0,217,255,0.7)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
        >
          <Play className="w-5 h-5 mr-2" />
          {isRunning ? '生成进行中...' : '开始生成'}
        </Button>

        <div className="text-xs text-slate-500 space-y-0.5">
          <p>• 预计时间: ~{Math.ceil(config.numSamples / (config.concurrency * 15))} 分钟</p>
          <p>• 目标样本: {config.numSamples} ({Math.floor(config.numSamples * (1 - config.multiRatio))} 单轮, {Math.floor(config.numSamples * config.multiRatio)} 多轮)</p>
        </div>
      </div>

      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-4xl max-h-[85vh] bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 border border-[#00d9ff]/20 shadow-[0_0_40px_rgba(0,217,255,0.15)] backdrop-blur-xl p-0 gap-0">
          <DialogHeader className="px-6 pt-6 pb-4 border-b border-slate-700/50">
            <DialogTitle className="text-slate-100 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[#00d9ff]/10 border border-[#00d9ff]/30">
                <Eye className="w-5 h-5 text-[#00d9ff]" />
              </div>
              <div className="flex-1">
                <div className="text-lg">文件预览</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">{config.toolListPath}</div>
              </div>
            </DialogTitle>
          </DialogHeader>
          <div className="px-4 py-3">
            <div className="relative rounded-xl border border-slate-700/20 shadow-inner">
              <div className="absolute top-0 left-0 right-0 h-10 bg-gradient-to-b from-slate-900/80 to-transparent pointer-events-none z-10" />
              <pre className="bg-slate-950/50 p-6 overflow-auto max-h-[calc(85vh-180px)] text-slate-300 leading-relaxed whitespace-pre-wrap break-words
                scrollbar-thin scrollbar-track-slate-900/50 scrollbar-thumb-slate-700 hover:scrollbar-thumb-slate-600
                [&::-webkit-scrollbar]:w-2
                [&::-webkit-scrollbar-track]:bg-slate-900/50
                [&::-webkit-scrollbar-track]:rounded-full
                [&::-webkit-scrollbar-thumb]:bg-slate-700
                [&::-webkit-scrollbar-thumb]:rounded-full
                [&::-webkit-scrollbar-thumb]:hover:bg-slate-600
                [&::-webkit-scrollbar]:h-2">
                <code className="text-sm font-mono">{previewContent}</code>
              </pre>
            </div>
          </div>
          <div className="px-6 pb-6 pt-2 flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setPreviewOpen(false)}
              className="bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-slate-100 hover:border-[#00d9ff]/50"
            >
              关闭
            </Button>
            <Button
              onClick={() => {
                navigator.clipboard.writeText(previewContent);
              }}
              className="bg-gradient-to-r from-[#00d9ff]/90 to-[#0066ff]/90 hover:from-[#00d9ff] hover:to-[#0066ff] text-slate-900 shadow-[0_0_15px_rgba(0,217,255,0.3)] hover:shadow-[0_0_25px_rgba(0,217,255,0.5)]"
            >
              复制内容
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
