### 테스트 1

배고픔 9, 주변에 창고 1개. 평균 응답시간 6.5초

```
{
"agent":
{
"name": "John",
"state": {
"hunger": 9,
 "sleepiness": 2,
 "loneliness": 3,
 },
"current_location": "John's home",
"personality": "introverted, practical, punctual",
        "visible_interactables": [
          {
            "location": "storage",
            "interactable": [
              "old_blueprint", "vegetable_seeds",
            ]
          }
        ],
        "locations_in_section": [],      }
}
```

```json
{
  "action": "move",
  "details": {
    "location": "storage",
    "target": "vegetable_seeds"
  },
  "reason": "John is very hungry and could use the vegetable seeds to try to grow some food."
}
```

### 테스트 2

배고픔 9, 주변에 창고, 집 . 평균 응답시간 6.5초

```
{
  "agent": {
    "name": "John",
    "state": {
      "hunger": 9,
      "sleepiness": 2,
      "loneliness": 3
    },
    "current_location": "park",
    "personality": "introverted, practical, punctual",
    "visible_interactables": [
      {
        "location": "storage",
        "interactable": ["old_blueprint", "vegetable_seeds"]
      },
      {
        "location": "house",
        "interactable": ["bookshelf", "bed"]
      },
      {
        "location": "park",
        "interactable": ["fountain"]
      }
    ],
    "locations_in_section": []
  }
}

```

```json
{
  "action": "interact",
  "details": {
    "location": "storage",
    "target": "vegetable_seeds"
  },
  "reason": "John is very hungry and might be able to find something useful to eat or grow."
}
```
