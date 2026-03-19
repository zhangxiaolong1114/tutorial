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
    email: '邮箱',
    password: '密码',
    confirmPassword: '确认密码',
    loginButton: '登 录',
    registerButton: '注 册',
    noAccount: '还没有账号？',
    hasAccount: '已有账号？',
    goRegister: '去注册',
    goLogin: '去登录',
    emailPlaceholder: '请输入邮箱',
    passwordPlaceholder: '请输入密码',
    confirmPasswordPlaceholder: '请再次输入密码'
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

// 英文语言包（预留）
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
    email: 'Email',
    password: 'Password',
    confirmPassword: 'Confirm Password',
    loginButton: 'Login',
    registerButton: 'Register',
    noAccount: "Don't have an account?",
    hasAccount: 'Already have an account?',
    goRegister: 'Sign up',
    goLogin: 'Sign in',
    emailPlaceholder: 'Enter your email',
    passwordPlaceholder: 'Enter your password',
    confirmPasswordPlaceholder: 'Confirm your password'
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
