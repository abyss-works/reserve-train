<script setup lang="ts">
import type { Train } from '@/types'

const props = defineProps<{ train: Train; selected?: boolean }>()
const emit = defineEmits<{ select: []; autoMonitor: [] }>()

const generalSoldOut = !props.train.general_available && !props.train.waiting_possible
</script>

<template>
  <v-card
    :variant="selected ? 'tonal' : 'elevated'"
    :color="selected ? 'primary' : undefined"
    :class="selected ? '' : 'bg-surface'"
    hover
    @click="emit('select')"
  >
    <v-card-text class="pa-4">
      <!-- Header -->
      <div class="d-flex align-center ga-2 mb-2">
        <span class="text-body-2 font-weight-bold">{{ train.train_type }}</span>
        <span class="text-caption text-medium-emphasis">#{{ train.train_no }}</span>
        <v-spacer />
        <v-chip size="x-small" variant="tonal" label>{{ train.duration }}</v-chip>
      </div>

      <!-- Route -->
      <div class="d-flex align-center mb-2">
        <div class="text-center" style="min-width: 56px;">
          <div class="text-h6 font-weight-bold">{{ train.dep_display }}</div>
          <div class="text-caption text-medium-emphasis">{{ train.dep_name }}</div>
        </div>
        <div class="flex-grow-1 mx-2 d-flex align-center">
          <v-divider thickness="2" class="border-dashed" />
          <v-icon small color="grey" class="mx-1">mdi-arrow-right</v-icon>
          <v-divider thickness="2" class="border-dashed" />
        </div>
        <div class="text-center" style="min-width: 56px;">
          <div class="text-h6 font-weight-bold">{{ train.arr_display }}</div>
          <div class="text-caption text-medium-emphasis">{{ train.arr_name }}</div>
        </div>
      </div>

      <!-- Seat status -->
      <div class="d-flex ga-3 text-caption">
        <div class="d-flex align-center ga-1">
          <v-icon :color="train.general_available ? 'success' : train.waiting_possible ? 'warning' : 'error'" size="x-small">mdi-circle</v-icon>
          <span class="text-medium-emphasis">일반실</span>
          <span :class="train.general_available ? 'text-success' : train.waiting_possible ? 'text-warning' : 'text-error'">
            {{ train.general_available ? '가능' : train.waiting_possible ? '대기' : '매진' }}
          </span>
        </div>
        <div v-if="train.train_type === 'KTX' || train.train_type === 'KTX-산천'" class="d-flex align-center ga-1">
          <v-icon :color="train.special_available ? 'success' : 'error'" size="x-small">mdi-circle</v-icon>
          <span class="text-medium-emphasis">특실</span>
          <span :class="train.special_available ? 'text-success' : 'text-error'">{{ train.special_available ? '가능' : '매진' }}</span>
        </div>
      </div>
    </v-card-text>

    <!-- Auto-reserve (sold out only) -->
    <v-divider v-if="generalSoldOut" />
    <v-card-actions v-if="generalSoldOut" class="pa-2">
      <v-btn variant="text" color="grey" size="small" block class="text-caption" @click.stop="emit('autoMonitor')">
        <v-icon start size="x-small">mdi-clock-outline</v-icon> 자동 예매
      </v-btn>
    </v-card-actions>
  </v-card>
</template>
