/**
 * 设备指纹工具
 * 用于生成唯一的设备标识
 */

export function generateDeviceFingerprint(): string {
  // 组合多个浏览器特征来生成设备指纹
  const features = [
    navigator.userAgent,
    navigator.language,
    screen.colorDepth,
    screen.width + 'x' + screen.height,
    new Date().getTimezoneOffset(),
    !!window.sessionStorage,
    !!window.localStorage,
    navigator.hardwareConcurrency || 'unknown',
    navigator.platform || 'unknown'
  ]
  
  // 简单哈希
  const str = features.join('###')
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // 转换为32位整数
  }
  
  return Math.abs(hash).toString(16)
}

// 获取或创建设备指纹
export function getDeviceFingerprint(): string {
  const storageKey = 'device_fingerprint'
  let fingerprint = localStorage.getItem(storageKey)
  
  if (!fingerprint) {
    fingerprint = generateDeviceFingerprint()
    localStorage.setItem(storageKey, fingerprint)
  }
  
  return fingerprint
}
