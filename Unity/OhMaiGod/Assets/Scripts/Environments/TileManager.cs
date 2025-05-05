using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Tilemaps;
public class TileManager : MonoBehaviour
{
    private static TileManager mInstance;

    [Header("Tilemaps")]
    [SerializeField] private Tilemap mGroundTilemap;    // 바닥 타일맵 (기본 맵 전체 영역)
    private List<Tilemap> mLocationTilemaps;            // 구역 타일맵 (구역 나누기)
    private List<TileController> mTileTree;

    [Header("Layer Masks")]
    [SerializeField] private LayerMask mWallLayerMask;        // 벽 레이어 마스크
    [SerializeField] private LayerMask mObjectLayerMask;      // 오브젝트 레이어 마스크
    [SerializeField] private LayerMask mNPCLayerMask;         // NPC 레이어 마스크

    [Header("Debug")]
    [SerializeField] private bool mShowDebug = true;
    public bool mIsInitialized = false;



    // 싱글톤 인스턴스를 반환하는 프로퍼티
    public static TileManager Instance { 
        get { return mInstance; }
    }

    private void Awake()
    {
        mInstance = this;
        DontDestroyOnLoad(gameObject);
        mLocationTilemaps = new List<Tilemap>();
        mTileTree = new List<TileController>();
        mIsInitialized = true;
    }

    // 디버깅
    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space))
        {
            Debug.Log($"타일맵트리");
            foreach (var tileController in mTileTree)
            {
                Debug.Log($"타일맵 : {tileController.LocationName}");
                foreach (var childInteractable in tileController.ChildInteractables)
                {
                    Debug.Log($"오브젝트 : {childInteractable.InteractableName}");
                }
            }
        }
    }

    public Tilemap GroundTilemap { get { return mGroundTilemap; } }

    public LayerMask WallLayerMask { get { return mWallLayerMask; } }
    public LayerMask ObjectLayerMask { get { return mObjectLayerMask; } }
    public LayerMask NPCLayerMask { get { return mNPCLayerMask; } }
    public LayerMask ObstacleLayerMask { get { return mWallLayerMask | mObjectLayerMask | mNPCLayerMask; } }

    public List<TileController> TileTree { get { return mTileTree; } }

    public TileController GetTileController(Vector3Int position)
    {
        foreach (var locationTilemap in mLocationTilemaps)
        {
            if (locationTilemap.HasTile(position))
            {
                TileController tileController = locationTilemap.GetComponent<TileController>();
                if (tileController != null)
                {
                    return tileController;
                }
            }
        }
        return null;
    }

    public TileController GetTileController(string locationName)
    {
        foreach (var locationTilemap in mLocationTilemaps)
        {
            if (locationTilemap.name == locationName)
            {
                return locationTilemap.GetComponent<TileController>();
            }
        }
        return null;
    }

    public List<string> GetLocationNames()
    {
        return mTileTree.Select(location => location.LocationName).ToList();
    }

    public void AddLocationTilemap(TileController tileController)
    {
        if (!mTileTree.Contains(tileController))
        {
            mTileTree.Add(tileController);
            mLocationTilemaps.Add(tileController.Tilemap);
        }
    }

    public void RemoveLocationTilemap(TileController tileController)
    {
        if (mTileTree.Contains(tileController))
        {
            mTileTree.Remove(tileController);
            mLocationTilemaps.Remove(tileController.Tilemap);
        }
    }
}