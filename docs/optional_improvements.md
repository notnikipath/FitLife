# Optional Improvements Mapping

## Group A

1. Exercise recognition by sensor/camera proxy endpoint: `/activities/recognize`
2. Personal load recommendations: `/analytics/recommendations/{user_id}`
3. AR coach: planned extension point in mobile module
4. Technique analysis: can be attached to recognition payload parser

## Group B

1. Wearable integrations: Garmin/Fitbit/Apple Health via `/activities/wearables/sync`
2. MyFitnessPal sync: `/integrations/myfitnesspal/sync`
3. Calendar integration: can be added through gateway reminders
4. Excel export: `/export/{user_id}/excel`

## Group C

1. Video caching strategy: `/cache/video-plan`
2. Parallel processing plan for device streams: `/processing/parallel-plan`
3. User sharding plan: `/analytics/sharding-plan`
4. Async statistics recalculation: `/analytics/async-recalc`

## Group D

1. Mobile offline architecture in `mobile/README.md`
2. Voice coach reserved as mobile extension
3. Video calls can be integrated as a dedicated future service
4. Gamification active with achievements/challenges/feed mechanics
