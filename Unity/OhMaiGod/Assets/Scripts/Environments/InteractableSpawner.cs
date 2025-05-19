using System.Collections.Generic;
using UnityEngine;
using System.Linq;

public class InteractableSpawner : MonoBehaviour
{
    [Header("Spawner Settings")]
    [Tooltip("이 타일에 생성될 수 있는 아이템 목록")]
    [SerializeField] private List<GameObject> mInteractablePrefabs;
    [Tooltip("생성 간격 (분 - 게임 시간)")]
    [SerializeField] private int mSpawnTime;
    [Tooltip("생성 확률 (0~1)")]
    [SerializeField] private float mSpawnProbability;

    private double mLastSpawnGameMinutes = 0;
    private TileController mTileController;

    void Awake()
    {
        mTileController = GetComponent<TileController>();
        if (mTileController == null)
        {
            LogManager.Log("Spawner", "TileController를 찾을 수 없습니다.", 0);
        }
        mLastSpawnGameMinutes = TimeManager.Instance.GetCurrentGameTime().TotalMinutes;
    }

    void Update()
    {
        double currentGameMinutes = TimeManager.Instance.GetCurrentGameTime().TotalMinutes;
        if (currentGameMinutes - mLastSpawnGameMinutes >= mSpawnTime)
        {
            mLastSpawnGameMinutes = currentGameMinutes;
            TrySpawnInteractable();
        }
    }

    private void TrySpawnInteractable()
    {
        if (mTileController == null) return;

        // 확률 체크
        if (Random.value > mSpawnProbability) return;

        // 빈 위치 찾기 (AllLayerMask와 겹치지 않는 위치만)
        List<Vector2> candidatePositions = new List<Vector2>();
        Vector2 spawnPos = Vector2.zero;
        if (mTileController.Tilemap != null)
        {
            BoundsInt bounds = mTileController.Tilemap.cellBounds;
            for (int x = bounds.min.x; x < bounds.max.x; x++)
            {
                for (int y = bounds.min.y; y < bounds.max.y; y++)
                {
                    Vector3Int cell = new Vector3Int(x, y, 0);
                    if (mTileController.Tilemap.HasTile(cell))
                    {
                        Vector2 worldPos = mTileController.Tilemap.GetCellCenterWorld(cell);
                        // 해당 위치에 장애물이 없고 시야 바깥이면 후보에 추가
                        bool hasAny = Physics2D.OverlapCircle(worldPos, 0.2f, TileManager.Instance.AllLayerMask);
                        bool hasVision = Physics2D.OverlapCircle(worldPos, 0.2f, TileManager.Instance.VisionLayerMask);
                        if (!hasAny && !hasVision)
                        {
                            candidatePositions.Add(worldPos);
                        }
                    }
                }
            }
        }
        if (candidatePositions.Count > 0)
        {
            spawnPos = candidatePositions[Random.Range(0, candidatePositions.Count)];
        }
        if (spawnPos == Vector2.zero)
        {
            LogManager.Log("Env", "스폰 가능한 위치가 없습니다.", 2);
            return;
        }
        // 생성
        Spawn(spawnPos);
    }

    public string Spawn(Vector2 _spawnPos)
    {
        // 프리팹 랜덤 선택
        if (mInteractablePrefabs == null || mInteractablePrefabs.Count == 0) return "";
        GameObject prefab = mInteractablePrefabs[Random.Range(0, mInteractablePrefabs.Count)];

        // 스폰
        Interactable interactable = Instantiate(prefab, _spawnPos, Quaternion.identity).GetComponent<Interactable>();
        LogManager.Log("Env", $"{interactable.InteractableName}을(를) {_spawnPos}에 스폰했습니다.", 2);
        return interactable.InteractableName;
    }
}
