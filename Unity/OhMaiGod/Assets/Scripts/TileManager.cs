using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;
public class TileManager : MonoBehaviour
{
    private static TileManager mInstance;
    [SerializeField] private Tilemap mGroundTilemap;    // 바닥 타일맵 (기본 맵 전체 영역)
    [SerializeField] private Tilemap mWallTilemap;      // 벽 타일맵 (벽, collider 적용, 충돌 판정)
    [SerializeField] private List<Tilemap> mSectionTilemaps;   // 구역 타일맵 (구역 나누기)
    [SerializeField] private LayerMask mWallLayerMask;        // 벽 레이어 마스크
    [SerializeField] private LayerMask mObjectLayerMask;      // 오브젝트 레이어 마스크
    [SerializeField] private LayerMask mNPCLayerMask;         // NPC 레이어 마스크

    // 싱글톤 인스턴스를 반환하는 프로퍼티
    public static TileManager Instance { 
        get { return mInstance; }
    }

    private void Awake()
    {
        mInstance = this;
        DontDestroyOnLoad(gameObject);
    }

    public Tilemap GroundTilemap { get { return mGroundTilemap; } }
    public Tilemap WallTilemap { get { return mWallTilemap; } }
    public List<Tilemap> SectionTilemaps { get { return mSectionTilemaps; } }
    public LayerMask WallLayerMask { get { return mWallLayerMask; } }
    public LayerMask ObjectLayerMask { get { return mObjectLayerMask; } }
    public LayerMask NPCLayerMask { get { return mNPCLayerMask; } }
    public LayerMask ObstacleLayerMask { get { return mWallLayerMask | mObjectLayerMask | mNPCLayerMask; } }

    public void AddSectionTilemap(Tilemap _tilemap)
    {
        if (!_tilemap.isActiveAndEnabled)
        {
            _tilemap.gameObject.SetActive(true);
        }
        else
        {
            mSectionTilemaps.Add(_tilemap);
        }
    }

    public void RemoveSectionTilemap(Tilemap _tilemap)
    {
        if (_tilemap.isActiveAndEnabled)
        {
            _tilemap.gameObject.SetActive(false);
        }
        else
        {
            mSectionTilemaps.Remove(_tilemap);
        }
    }
}