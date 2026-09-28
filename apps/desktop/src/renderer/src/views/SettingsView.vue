<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import {
  fetchLlmConfigStatus,
  getTeacherAuth,
  retryTeacher,
  saveLlmApiKey,
  TeacherApiError,
  type TeacherAuth
} from '../services/teacherClient'

const auth = ref<TeacherAuth>({ state: 'starting', base_url: '', bearer: null })
const configured = ref(false)
const llmApiKey = ref('')
const validationError = ref<string | null>(null)
const saveError = ref<string | null>(null)
const loadError = ref<string | null>(null)
const saving = ref(false)
const loading = ref(true)

const dirty = computed(() => llmApiKey.value.trim().length > 0)

const launchFailureMessage = computed(
  () => auth.value.message ?? 'Не удаётся подключиться к учителю'
)

async function loadLlmStatus(): Promise<void> {
  loadError.value = null
  if (auth.value.state !== 'running') {
    return
  }
  try {
    const status = await fetchLlmConfigStatus(auth.value)
    configured.value = status.configured
  } catch (err) {
    loadError.value =
      err instanceof TeacherApiError ? err.message : 'Не удалось загрузить статус ключа'
  }
}

async function refreshStatus(): Promise<void> {
  loading.value = true
  try {
    auth.value = await getTeacherAuth()
    await loadLlmStatus()
  } finally {
    loading.value = false
  }
}

async function retry(): Promise<void> {
  loading.value = true
  try {
    auth.value = await retryTeacher()
    await loadLlmStatus()
  } finally {
    loading.value = false
  }
}

async function save(): Promise<void> {
  if (saving.value) {
    return
  }
  validationError.value = null
  saveError.value = null
  const trimmed = llmApiKey.value.trim()
  if (!trimmed) {
    validationError.value = 'Введите ключ — пустое значение не сохраняется'
    return
  }
  if (auth.value.state !== 'running') {
    saveError.value = 'Учитель не запущен — сохранение недоступно'
    return
  }
  saving.value = true
  try {
    const result = await saveLlmApiKey(auth.value, trimmed)
    configured.value = result.configured
    llmApiKey.value = ''
  } catch (err) {
    saveError.value =
      err instanceof TeacherApiError ? err.message : 'Не удалось сохранить ключ'
  } finally {
    saving.value = false
  }
}

let unsubscribe: (() => void) | undefined

onMounted(() => {
  void refreshStatus()
  if (typeof window !== 'undefined' && window.teacher) {
    unsubscribe = window.teacher.onStatusChange((status) => {
      auth.value = status
      if (status.state === 'running') {
        void loadLlmStatus()
      }
    })
  }
})

onUnmounted(() => {
  unsubscribe?.()
})

// LEAVE_DIRTY: unsaved LLM edits must never silently persist or be silently
// discarded — confirm before leaving; stay on cancel.
onBeforeRouteLeave(() => {
  if (!dirty.value) {
    return true
  }
  return window.confirm(
    'Есть несохранённые изменения в LLM/API. Уйти без сохранения?'
  )
})
</script>

<template>
  <main class="settings" data-testid="settings-view" aria-label="Настройки">
    <div class="scroll">
      <h1 class="page-title">Настройки</h1>

      <p v-if="auth.state === 'starting'" class="hint" data-testid="connecting-hint">
        Подключение к учителю…
      </p>
      <div
        v-else-if="auth.state !== 'running'"
        class="banner"
        role="alert"
        data-testid="launch-failure-banner"
      >
        <p>{{ launchFailureMessage }}</p>
        <button type="button" class="secondary" @click="retry">Повторить</button>
      </div>

      <section class="settings-section" aria-labelledby="section-telegram">
        <span class="accent-rule" aria-hidden="true" />
        <p id="section-telegram" class="kicker">TELEGRAM</p>
        <p class="status">Статус: не привязан</p>
        <p class="hint">
          Свяжите Telegram, чтобы получать напоминания о занятиях и мини-уроки в течение дня.
        </p>
        <button type="button" class="cta" disabled title="Появится в Epic 4">
          Привязать
        </button>
      </section>

      <section class="settings-section" aria-labelledby="section-voice">
        <span class="accent-rule" aria-hidden="true" />
        <p id="section-voice" class="kicker">ГОЛОС</p>
        <p class="hint">
          Режим микрофона (нажать-и-говорить или автопрослушивание) и выбор устройства
          появятся здесь.
        </p>
      </section>

      <section class="settings-section" aria-labelledby="section-schedule">
        <span class="accent-rule" aria-hidden="true" />
        <p id="section-schedule" class="kicker">РАСПИСАНИЕ И ДЛИТЕЛЬНОСТЬ</p>
        <p class="hint">Текущее расписание и длительность уроков появятся здесь.</p>
        <button type="button" class="secondary" disabled title="Появится в Epic 2">
          Изменить
        </button>
      </section>

      <section class="settings-section" aria-labelledby="section-goals">
        <span class="accent-rule" aria-hidden="true" />
        <p id="section-goals" class="kicker">ЦЕЛИ И АКЦЕНТЫ</p>
        <p class="hint">Учебные цели и смысловые акценты появятся здесь.</p>
      </section>

      <section class="settings-section" aria-labelledby="section-llm">
        <span class="accent-rule" aria-hidden="true" />
        <p id="section-llm" class="kicker">LLM / API</p>
        <p v-if="configured" class="hint" data-testid="llm-configured-hint">
          Ключ уже сохранён. Введите новый, чтобы заменить его.
        </p>
        <p v-else class="hint" data-testid="llm-unconfigured-hint">Ключ ещё не сохранён.</p>
        <label class="field-label" for="llm-api-key">Ключ API</label>
        <input
          id="llm-api-key"
          v-model="llmApiKey"
          class="field"
          type="password"
          autocomplete="off"
          placeholder="sk-..."
          :disabled="auth.state !== 'running' || saving"
        />
        <p v-if="validationError" class="error" role="alert" data-testid="validation-error">
          {{ validationError }}
        </p>
        <p v-if="saveError" class="error" role="alert" data-testid="save-error">
          {{ saveError }}
        </p>
        <p v-if="loadError" class="error" role="alert" data-testid="load-error">
          {{ loadError }}
        </p>
        <button
          type="button"
          class="cta"
          data-testid="save-llm-button"
          :disabled="saving || auth.state !== 'running' || loading"
          @click="save"
        >
          Сохранить
        </button>
      </section>
    </div>
  </main>
</template>

<style scoped>
.settings {
  flex: 1;
  display: flex;
  min-height: 0;
  min-width: 0;
  background: var(--color-bg);
  color: var(--color-ink);
  overflow: auto;
}

.scroll {
  flex: 1;
  max-width: 640px;
  margin: 0 auto;
  padding: 24px 20px 48px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  background: var(--color-coral-soft);
  border: 1px solid var(--color-coral);
  border-radius: var(--radius-md);
}

.banner p {
  margin: 0;
  font-size: 13px;
  color: var(--color-ink);
}

.settings-section {
  position: relative;
  padding: 16px 18px 18px;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.accent-rule {
  display: block;
  width: 24px;
  height: 3px;
  background: var(--color-coral);
  border-radius: 2px;
  margin-bottom: 2px;
}

.kicker {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--color-muted);
  text-transform: uppercase;
}

.status {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink);
}

.hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: var(--color-muted);
}

.field-label {
  font-size: 12px;
  color: var(--color-muted);
}

.field {
  padding: 8px 10px;
  font: inherit;
  font-size: 13px;
  color: var(--color-ink);
  background: var(--color-bg);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
}

.field:disabled {
  opacity: 0.6;
}

.error {
  margin: 0;
  font-size: 12px;
  color: var(--color-missed);
}

.cta,
.secondary {
  align-self: flex-start;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 7px 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
}

.cta {
  color: var(--color-on-coral);
  background: var(--color-coral-cta);
  border: 1px solid var(--color-coral-cta);
}

.cta:disabled,
.secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary {
  color: var(--color-ink);
  background: var(--color-surface);
  border: 1px solid var(--color-line);
}

.cta:focus-visible,
.secondary:focus-visible {
  outline: 2px solid var(--color-coral);
  outline-offset: -2px;
}
</style>
