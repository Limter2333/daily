import { useState, useEffect } from 'react';
import {
  Sun,
  Moon,
  RefreshCw,
  Send,
  Calendar,
  FileText,
} from 'lucide-react';
import { getBriefings, generateBriefing, triggerSend } from '../services/api';
import type { Briefing, BriefingType } from '../types';

export default function BriefingView() {
  const [briefings, setBriefings] = useState<Briefing[]>([]);
  const [selectedBriefing, setSelectedBriefing] = useState<Briefing | null>(null);
  const [activeTab, setActiveTab] = useState<BriefingType>('morning');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [sending, setSending] = useState(false);

  // 加载早报/晚报列表
  const loadBriefings = async () => {
    try {
      setLoading(true);
      const response = await getBriefings(activeTab, 1, 20);
      setBriefings(response.items);

      // 如果有数据，选中第一个
      if (response.items.length > 0) {
        setSelectedBriefing(response.items[0]);
      } else {
        setSelectedBriefing(null);
      }
    } catch (error) {
      console.error('加载早报晚报失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBriefings();
  }, [activeTab]);

  // 生成早报/晚报
  const handleGenerate = async () => {
    try {
      setGenerating(true);
      await generateBriefing(activeTab);
      await loadBriefings();
    } catch (error) {
      console.error('生成失败:', error);
    } finally {
      setGenerating(false);
    }
  };

  // 发送早报/晚报
  const handleSend = async () => {
    try {
      setSending(true);
      await triggerSend(activeTab);
      alert('发送成功！');
    } catch (error) {
      console.error('发送失败:', error);
      alert('发送失败，请检查设置');
    } finally {
      setSending(false);
    }
  };

  // 格式化日期
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 渲染内容（保留换行和格式）
  const renderContent = (content: string) => {
    return content.split('\n').map((line, index) => {
      // 标题行
      if (line.startsWith('🌅') || line.startsWith('🌆')) {
        return (
          <h2 key={index} className="text-lg font-bold text-gray-900 mt-4 mb-2">
            {line}
          </h2>
        );
      }

      // 分类标题
      if (
        line.startsWith('💰') ||
        line.startsWith('💻') ||
        line.startsWith('🔬') ||
        line.startsWith('🤖') ||
        line.startsWith('🛒') ||
        line.startsWith('📰')
      ) {
        return (
          <h3
            key={index}
            className="text-base font-semibold text-primary-700 mt-4 mb-2"
          >
            {line}
          </h3>
        );
      }

      // 分隔线
      if (line.startsWith('─') || line.startsWith('═')) {
        return <hr key={index} className="my-2 border-gray-200" />;
      }

      // 统计行
      if (line.startsWith('📊') || line.startsWith('📈')) {
        return (
          <p key={index} className="text-sm text-gray-500 mt-2">
            {line}
          </p>
        );
      }

      // 链接行
      if (line.includes('🔗')) {
        const parts = line.split('🔗');
        const url = parts[1]?.trim();
        return (
          <p key={index} className="text-sm text-gray-600 mb-1">
            {parts[0]}
            {url && (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:underline ml-1"
              >
                阅读原文
              </a>
            )}
          </p>
        );
      }

      // 普通行
      if (line.trim()) {
        return (
          <p key={index} className="text-sm text-gray-700 mb-1">
            {line}
          </p>
        );
      }

      return <br key={index} />;
    });
  };

  return (
    <div className="container-responsive">
      {/* 标题区域 */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">📰 早报晚报</h2>
            <p className="mt-1 text-gray-500">查看每日生成的早报和晚报</p>
          </div>

          <div className="mt-4 md:mt-0 flex items-center space-x-3">
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              <FileText className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
              <span>{generating ? '生成中...' : '立即生成'}</span>
            </button>

            <button
              onClick={handleSend}
              disabled={sending || !selectedBriefing}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              <Send className={`w-4 h-4 ${sending ? 'animate-pulse' : ''}`} />
              <span>{sending ? '发送中...' : '发送推送'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 标签页 */}
      <div className="bg-white rounded-xl shadow-sm mb-6">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('morning')}
            className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'morning'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Sun className="w-4 h-4" />
            <span>早报</span>
          </button>

          <button
            onClick={() => setActiveTab('evening')}
            className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'evening'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Moon className="w-4 h-4" />
            <span>晚报</span>
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 左侧：列表 */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-medium text-gray-900">历史记录</h3>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="w-6 h-6 text-primary-600 animate-spin" />
              </div>
            ) : briefings.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                <Calendar className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>暂无{activeTab === 'morning' ? '早报' : '晚报'}</p>
                <p className="text-sm mt-1">点击"立即生成"创建</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
                {briefings.map((briefing) => (
                  <button
                    key={briefing.id}
                    onClick={() => setSelectedBriefing(briefing)}
                    className={`w-full text-left p-4 hover:bg-gray-50 transition-colors ${
                      selectedBriefing?.id === briefing.id
                        ? 'bg-primary-50 border-l-4 border-primary-600'
                        : ''
                    }`}
                  >
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {briefing.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDate(briefing.created_at)}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 右侧：内容 */}
        <div className="lg:col-span-3">
          {selectedBriefing ? (
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              {/* 标题 */}
              <div
                className={`p-6 text-white ${
                  activeTab === 'morning'
                    ? 'gradient-bg'
                    : 'gradient-bg-evening'
                }`}
              >
                <h2 className="text-2xl font-bold">{selectedBriefing.title}</h2>
                <p className="mt-2 opacity-90">
                  {formatDate(selectedBriefing.created_at)}
                </p>
              </div>

              {/* 内容 */}
              <div className="p-6">{renderContent(selectedBriefing.content)}</div>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                暂无内容
              </h3>
              <p className="text-gray-500">
                选择一个{activeTab === 'morning' ? '早报' : '晚报'}查看，或点击"立即生成"
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
