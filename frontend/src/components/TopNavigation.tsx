import { Avatar, AvatarFallback } from './ui/avatar';
import { Badge } from './ui/badge';
import { Activity } from 'lucide-react';
import type { ProcessState } from '../App';

interface TopNavigationProps {
  processState: ProcessState;
}

export function TopNavigation({ processState }: TopNavigationProps) {
  const getStatusColor = () => {
    switch (processState) {
      case '运行中':
        return 'bg-[#00d9ff] shadow-[0_0_10px_#00d9ff]';
      case '验证中':
        return 'bg-yellow-400 shadow-[0_0_10px_#facc15]';
      case '已完成':
        return 'bg-green-400 shadow-[0_0_10px_#4ade80]';
      default:
        return 'bg-slate-500';
    }
  };

  const getStatusVariant = () => {
    switch (processState) {
      case '运行中':
        return 'default';
      case '验证中':
        return 'secondary';
      case '已完成':
        return 'default';
      default:
        return 'outline';
    }
  };

  return (
    <nav className="h-16 border-b border-slate-700/50 bg-[#0f172a]/80 backdrop-blur-sm px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#00d9ff] to-[#0066ff] flex items-center justify-center shadow-[0_0_20px_rgba(0,217,255,0.5)]">
          <Activity className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-slate-100 tracking-wide">AutoToolDPO 数据生成控制台</h1>
          <p className="text-xs text-slate-400">赋范空间 by muyan</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <Badge 
          variant={getStatusVariant()}
          className={`px-4 py-1 ${
            processState === '运行中' ? 'bg-[#00d9ff] text-slate-900 hover:bg-[#00d9ff]' : ''
          } ${
            processState === '验证中' ? 'bg-yellow-400 text-slate-900 hover:bg-yellow-400' : ''
          } ${
            processState === '已完成' ? 'bg-green-400 text-slate-900 hover:bg-green-400' : ''
          }`}
        >
          <div className={`w-2 h-2 rounded-full mr-2 inline-block ${getStatusColor()}`} />
          {processState}
        </Badge>

        <Avatar className="w-9 h-9 border-2 border-slate-600">
          <AvatarFallback className="bg-gradient-to-br from-slate-700 to-slate-800 text-slate-200">
            AD
          </AvatarFallback>
        </Avatar>
      </div>
    </nav>
  );
}
