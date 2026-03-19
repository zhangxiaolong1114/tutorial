<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center mb-6">
      <button
        @click="$router.back()"
        class="mr-4 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
      >
        ← {{ $t('common.back') }}
      </button>
      <h1 class="text-2xl font-bold text-gray-900">{{ document.title }}</h1>
    </div>
    
    <div class="bg-white rounded-xl shadow-sm p-8">
      <div class="flex items-center justify-between mb-6 text-sm text-gray-600">
        <span>{{ $t('generate.courseName') }}: {{ document.course }}</span>
        <span>{{ $t('document.createTime') }}: {{ document.createdAt }}</span>
      </div>
      
      <div class="space-y-8">
        <section>
          <h2 class="text-xl font-bold text-gray-900 mb-4 pb-2 border-b">{{ $t('document.sections.concept') }}</h2>
          <div class="prose max-w-none text-gray-700" v-html="document.content.concept"></div>
        </section>
        
        <section>
          <h2 class="text-xl font-bold text-gray-900 mb-4 pb-2 border-b">{{ $t('document.sections.explanation') }}</h2>
          <div class="prose max-w-none text-gray-700" v-html="document.content.explanation"></div>
        </section>
        
        <section>
          <h2 class="text-xl font-bold text-gray-900 mb-4 pb-2 border-b">{{ $t('document.sections.keyPoints') }}</h2>
          <div class="prose max-w-none text-gray-700" v-html="document.content.keyPoints"></div>
        </section>
        
        <section>
          <h2 class="text-xl font-bold text-gray-900 mb-4 pb-2 border-b">{{ $t('document.sections.simulation') }}</h2>
          <div class="bg-gray-100 rounded-lg p-8 text-center">
            <p class="text-gray-500">[{{ $t('document.sections.simulation') }}]</p>
          </div>
        </section>
        
        <section>
          <h2 class="text-xl font-bold text-gray-900 mb-4 pb-2 border-b">{{ $t('document.sections.summary') }}</h2>
          <div class="prose max-w-none text-gray-700" v-html="document.content.summary"></div>
        </section>
        
        <section>
          <h2 class="text-xl font-bold text-gray-900 mb-4 pb-2 border-b">{{ $t('document.sections.exercises') }}</h2>
          <div class="prose max-w-none text-gray-700" v-html="document.content.exercises"></div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const document = ref({
  id: route.params.id,
  title: '牛顿第二定律',
  course: '大学物理',
  createdAt: '2026-03-19',
  content: {
    concept: '<p>牛顿第二定律指出，物体的加速度与作用力成正比，与物体质量成反比。</p><p class="font-bold text-center my-4 text-lg">F = ma</p>',
    explanation: '<p>当一个力 F 作用在质量为 m 的物体上时，物体会产生加速度 a。这个加速度的方向与力的方向相同，大小与力的大小成正比，与物体质量成反比。</p>',
    keyPoints: '<ul><li>力是产生加速度的原因</li><li>加速度方向与合力方向相同</li><li>质量是物体惯性的量度</li></ul>',
    summary: '<p>牛顿第二定律是经典力学的核心，它定量地描述了力、质量和加速度之间的关系。</p>',
    exercises: '<div class="space-y-4"><div><p class="font-medium">1. 一个质量为 2kg 的物体受到 10N 的力，求加速度。</p><p class="text-gray-600 mt-2">解：a = F/m = 10/2 = 5 m/s²</p></div></div>'
  }
})
</script>
