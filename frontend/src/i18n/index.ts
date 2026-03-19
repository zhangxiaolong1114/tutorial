import { createI18n } from 'vue-i18n'

// 中文语言包
const zh = {
  app: {
    name: '智教云',
    title: 'AI 课程知识点生成平台'
  },
  nav: {
    generate: '生成文档',
    documents: '我的文档',
    logout: '退出登录',
    welcome: '欢迎'
  },
  auth: {
    login: '登录',
    register: '注册',
    username: '用户名',
    email: '邮箱',
    password: '密码',
    confirmPassword: '确认密码',
    newPassword: '新密码',
    verificationCode: '验证码',
    loginButton: '登 录',
    registerButton: '注 册',
    noAccount: '还没有账号？',
    hasAccount: '已有账号？',
    goRegister: '去注册',
    goLogin: '去登录',
    forgotPassword: '忘记密码？',
    resetPassword: '重置密码',
    resetPasswordButton: '重置密码',
    resetSuccess: '密码重置成功，请使用新密码登录',
    backToLogin: '返回登录',
    resetting: '重置中...',
    usernamePlaceholder: '请输入用户名',
    emailPlaceholder: '请输入邮箱',
    passwordPlaceholder: '请输入密码',
    newPasswordPlaceholder: '请输入新密码',
    confirmPasswordPlaceholder: '请再次输入密码',
    verificationCodePlaceholder: '请输入6位验证码',
    passwordMismatch: '两次输入的密码不一致',
    loggingIn: '登录中...',
    registering: '注册中...',
    sendCode: '发送验证码',
    resendCode: '重新发送',
    sending: '发送中...',
    emailRequired: '请输入邮箱地址',
    emailInvalid: '请输入有效的邮箱地址',
    verificationCodeError: '验证码错误或已过期',
    verificationCodeSent: '验证码已发送',
    verificationCodeRequired: '请先发送验证码'
  },
  generate: {
    title: '生成教学文档',
    courseName: '课程名称',
    coursePlaceholder: '例如：大学物理',
    knowledgePoint: '知识点',
    knowledgePlaceholder: '例如：牛顿第二定律',
    difficulty: '难度等级',
    difficultyEasy: '简单',
    difficultyMedium: '中等',
    difficultyHard: '困难',
    grade: '适用年级',
    gradePlaceholder: '例如：大一',
    generateButton: '开始生成',
    generating: '生成中...',
    tip: '输入课程和知识点，AI 将为您生成完整的教学文档'
  },
  document: {
    title: '我的文档',
    createTime: '创建时间',
    actions: '操作',
    view: '查看',
    edit: '编辑',
    delete: '删除',
    download: '下载',
    noDocuments: '暂无文档',
    createFirst: '去生成您的第一个文档',
    confirmDelete: '确定要删除这个文档吗？',
    sections: {
      concept: '知识点概念',
      explanation: '详细讲解',
      keyPoints: '重难点分析',
      simulation: '交互仿真',
      summary: '总结',
      exercises: '习题与答案'
    }
  },
  common: {
    confirm: '确定',
    cancel: '取消',
    save: '保存',
    close: '关闭',
    back: '返回',
    loading: '加载中...',
    error: '出错了',
    retry: '重试',
    empty: '暂无数据'
  }
}

// 英文语言包
const en = {
  app: {
    name: 'EduGen',
    title: 'AI Course Knowledge Generator'
  },
  nav: {
    generate: 'Generate',
    documents: 'My Documents',
    logout: 'Logout',
    welcome: 'Welcome'
  },
  auth: {
    login: 'Login',
    register: 'Register',
    username: 'Username',
    email: 'Email',
    password: 'Password',
    confirmPassword: 'Confirm Password',
    verificationCode: 'Verification Code',
    loginButton: 'Login',
    registerButton: 'Register',
    noAccount: "Don't have an account?",
    hasAccount: 'Already have an account?',
    goRegister: 'Sign up',
    goLogin: 'Sign in',
    usernamePlaceholder: 'Enter your username',
    emailPlaceholder: 'Enter your email',
    passwordPlaceholder: 'Enter your password',
    confirmPasswordPlaceholder: 'Confirm your password',
    verificationCodePlaceholder: 'Enter 6-digit code',
    passwordMismatch: 'Passwords do not match',
    loggingIn: 'Logging in...',
    registering: 'Registering...',
    sendCode: 'Send Code',
    resendCode: 'Resend',
    sending: 'Sending...',
    emailRequired: 'Please enter your email',
    emailInvalid: 'Please enter a valid email',
    passwordLogin: 'Password Login',
    codeLogin: 'Code Login',
    verificationCodeError: 'Invalid or expired verification code',
    verificationCodeSent: 'Verification code sent',
    verificationCodeRequired: 'Please send verification code first'
  },
  generate: {
    title: 'Generate Document',
    courseName: 'Course Name',
    coursePlaceholder: 'e.g., Physics',
    knowledgePoint: 'Knowledge Point',
    knowledgePlaceholder: "e.g., Newton's Second Law",
    difficulty: 'Difficulty',
    difficultyEasy: 'Easy',
    difficultyMedium: 'Medium',
    difficultyHard: 'Hard',
    grade: 'Grade Level',
    gradePlaceholder: 'e.g., Freshman',
    generateButton: 'Generate',
    generating: 'Generating...',
    tip: 'Enter course and knowledge point to generate a teaching document'
  },
  document: {
    title: 'My Documents',
    createTime: 'Created',
    actions: 'Actions',
    view: 'View',
    edit: 'Edit',
    delete: 'Delete',
    download: 'Download',
    noDocuments: 'No documents yet',
    createFirst: 'Generate your first document',
    confirmDelete: 'Are you sure to delete this document?',
    sections: {
      concept: 'Concept',
      explanation: 'Explanation',
      keyPoints: 'Key Points',
      simulation: 'Simulation',
      summary: 'Summary',
      exercises: 'Exercises'
    }
  },
  common: {
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    close: 'Close',
    back: 'Back',
    loading: 'Loading...',
    error: 'Error',
    retry: 'Retry',
    empty: 'No data'
  }
}

// 从本地存储读取语言设置，默认中文
const savedLocale = typeof localStorage !== 'undefined'
  ? localStorage.getItem('locale') || 'zh'
  : 'zh'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'zh',
  messages: {
    zh,
    en
  }
})

export default i18n
