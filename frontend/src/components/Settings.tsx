import { useState, useEffect } from 'react';
import {
  Save,
  RefreshCw,
  Mail,
  Bell,
  Clock,
  Globe,
  Key,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { getSettings, updateSettings, getSchedulerJobs, getAISettingsStatus } from '../services/api';
import type { Settings as SettingsType, SchedulerJob, AISettingsStatus } from '../types';

export default function Settings() {
  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [aiStatus, setAiStatus] = useState<AISettingsStatus | null>(null);
  const [jobs, setJobs] = useState<SchedulerJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 加载设置
  const loadSettings = async () => {
    try {
      setLoading(true);
      const [settingsData, jobsData, aiStatusData] = await Promise.all([
        getSettings(),
        getSchedulerJobs(),
        getAISettingsStatus(),
      ]);
      setSettings(settingsData);
      setJobs(jobsData);
      setAiStatus(aiStatusData);
    } catch (error) {
      console.error('加载设置失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  // 保存设置
  const handleSave = async () => {
    if (!settings) return;

    try {
      setSaving(true);
      await updateSettings(settings);
      setMessage({ type: 'success', text: '设置已保存' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      console.error('保存设置失败:', error);
      setMessage({ type: 'error', text: '保存失败，请重试' });
    } finally {
      setSaving(false);
    }
  };

  // 更新设置字段
  const updateField = (field: keyof SettingsType, value: any) => {
    if (!settings) return;
    setSettings({ ...settings, [field]: value });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
        <span className="ml-3 text-gray-500">加载中...</span>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="text-center py-20 text-gray-500">加载设置失败</div>
    );
  }

  return (
    <div className="container-responsive max-w-4xl">
      {/* 标题 */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">⚙️ 系统设置</h2>
            <p className="mt-1 text-gray-500">配置早报晚报系统参数</p>
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center space-x-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            <Save className={`w-4 h-4 ${saving ? 'animate-spin' : ''}`} />
            <span>{saving ? '保存中...' : '保存设置'}</span>
          </button>
        </div>

        {/* 提示消息 */}
        {message && (
          <div
            className={`mt-4 p-3 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {message.text}
          </div>
        )}
      </div>

      {/* 定时任务状态 */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Clock className="w-5 h-5 mr-2" />
          定时任务
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="border border-gray-200 rounded-lg p-4"
            >
              <p className="font-medium text-gray-900">{job.name}</p>
              <p className="text-sm text-gray-500 mt-1">
                下次运行: {job.next_run ? new Date(job.next_run).toLocaleString('zh-CN') : '未安排'}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 基本设置 */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Globe className="w-5 h-5 mr-2" />
          基本设置
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              城市（用于天气）
            </label>
            <input
              type="text"
              value={settings.weather_city}
              onChange={(e) => updateField('weather_city', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Beijing"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              早报时间
            </label>
            <input
              type="time"
              value={settings.morning_time}
              onChange={(e) => updateField('morning_time', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              晚报时间
            </label>
            <input
              type="time"
              value={settings.evening_time}
              onChange={(e) => updateField('evening_time', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* AI 配置状态（只读） */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Key className="w-5 h-5 mr-2" />
          AI 配置
        </h3>

        {aiStatus ? (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              {aiStatus.ai_available ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <XCircle className="w-5 h-5 text-red-500" />
              )}
              <span className={`font-medium ${aiStatus.ai_available ? 'text-green-700' : 'text-red-700'}`}>
                {aiStatus.ai_available ? 'AI 服务可用' : 'AI 服务不可用'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Provider:</span>
                <span className="ml-2 font-medium">{aiStatus.ai_provider}</span>
              </div>
              <div>
                <span className="text-gray-500">Model:</span>
                <span className="ml-2 font-medium">{aiStatus.ai_model}</span>
              </div>
              <div>
                <span className="text-gray-500">Base URL:</span>
                <span className="ml-2 font-medium">{aiStatus.ai_base_url || '默认'}</span>
              </div>
              <div>
                <span className="text-gray-500">API Key:</span>
                <span className="ml-2 font-medium">{aiStatus.ai_api_key_set ? '已配置' : '未配置'}</span>
              </div>
            </div>

            <p className="text-xs text-gray-500 mt-2 p-2 bg-gray-50 rounded">
              {aiStatus.message}
            </p>
          </div>
        ) : (
          <div className="text-gray-500">加载 AI 配置状态中...</div>
        )}
      </div>

      {/* 邮件配置 */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Mail className="w-5 h-5 mr-2" />
          邮件配置
        </h3>

        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="email_enabled"
              checked={settings.email_enabled}
              onChange={(e) => updateField('email_enabled', e.target.checked)}
              className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <label htmlFor="email_enabled" className="text-sm font-medium text-gray-700">
              启用邮件推送
            </label>
          </div>

          {settings.email_enabled && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-7">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SMTP 服务器
                </label>
                <input
                  type="text"
                  value={settings.smtp_server}
                  onChange={(e) => updateField('smtp_server', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="smtp.gmail.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SMTP 端口
                </label>
                <input
                  type="number"
                  value={settings.smtp_port}
                  onChange={(e) => updateField('smtp_port', parseInt(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="587"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  用户名
                </label>
                <input
                  type="text"
                  value={settings.smtp_username}
                  onChange={(e) => updateField('smtp_username', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="your-email@gmail.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  密码
                </label>
                <input
                  type="password"
                  value={settings.smtp_password}
                  onChange={(e) => updateField('smtp_password', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="应用专用密码"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  收件人邮箱
                </label>
                <input
                  type="email"
                  value={settings.email_recipient}
                  onChange={(e) => updateField('email_recipient', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="recipient@example.com"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 推送配置 */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Bell className="w-5 h-5 mr-2" />
          推送配置
        </h3>

        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="push_enabled"
              checked={settings.push_enabled}
              onChange={(e) => updateField('push_enabled', e.target.checked)}
              className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <label htmlFor="push_enabled" className="text-sm font-medium text-gray-700">
              启用推送通知
            </label>
          </div>

          {settings.push_enabled && (
            <div className="space-y-4 pl-7">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  推送平台
                </label>
                <select
                  value={settings.push_platform}
                  onChange={(e) => updateField('push_platform', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="wechat">企业微信</option>
                  <option value="dingtalk">钉钉</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Webhook URL
                </label>
                <input
                  type="text"
                  value={settings.push_webhook_url}
                  onChange={(e) => updateField('push_webhook_url', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 保存按钮 */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center space-x-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          <Save className={`w-5 h-5 ${saving ? 'animate-spin' : ''}`} />
          <span>{saving ? '保存中...' : '保存设置'}</span>
        </button>
      </div>
    </div>
  );
}
