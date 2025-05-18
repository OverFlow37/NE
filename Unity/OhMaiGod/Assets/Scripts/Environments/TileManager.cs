using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Tilemaps;
using System.Collections;
using UnityEngine.SceneManagement;

public class TileManager : MonoBehaviour, ISaveable
{
    private static TileManager mInstance;

    [Header("Tilemaps")]
    [SerializeField] private Tilemap mGroundTilemap;    // 바닥 타일맵 (기본 맵 전체 영역)
    private List<Tilemap> mLocationTilemaps;            // 구역 타일맵 (구역 나누기)
    private List<TileController> mTileTree;

    // Interactable 위치 추적을 위한 Dictionary
    private Dictionary<Interactable, string> mInteractableLocations = new Dictionary<Interactable, string>();

    [Header("Layer Masks")]
    [SerializeField] private LayerMask mWallLayerMask;        // 벽 레이어 마스크
    [SerializeField] private LayerMask mObjectLayerMask;      // 충돌 오브젝트 레이어 마스크
    [SerializeField] private LayerMask mItemLayerMask;         // 비충돌 아이템 레이어 마스크
    [SerializeField] private LayerMask mNPCLayerMask;         // NPC 레이어 마스크
    [SerializeField] private LayerMask mVisionLayerMask;      // 시야 레이어 마스크

    [Header("Debug")]
    [SerializeField] private bool mShowDebug = true;
    private bool mIsInitialized = false;
    private HashSet<Interactable> mPendingTargets = new HashSet<Interactable>();

    // Interactable 정보 저장용 struct
    [System.Serializable]
    public struct InteractableSaveData
    {
        public string mPrefabName;      // 프리팹 이름
        public Vector3 mPosition;       // 위치
    }

    // 리스트 직렬화용 래퍼 struct
    [System.Serializable]
    public struct InteractableSaveDataList
    {
        public List<InteractableSaveData> mList;
    }

    // 싱글톤 인스턴스를 반환하는 프로퍼티
    public static TileManager Instance { 
        get { return mInstance; }
    }

    // 초기화 완료 여부를 반환하는 프로퍼티
    public bool IsInitialized {
        get { return mIsInitialized; }
    }

    private void Awake()
    {
        if (mInstance != null && mInstance != this)
        {
            Destroy(gameObject);
            return;
        }
        mInstance = this;
        DontDestroyOnLoad(gameObject);
        mLocationTilemaps = new List<Tilemap>();
        mTileTree = new List<TileController>();
        
        // 씬 로드 이벤트 등록
        SceneManager.sceneLoaded += OnSceneLoaded;

        // Awake에서는 초기화하지 않음
        StartCoroutine(InitializeManager());
    }

    private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        mIsInitialized = false;

        if (scene.name == "Main")
        {
            // ground tilemap 설정
            GameObject landBaseObj = GameObject.Find("Tilemap_land_base");
            if (landBaseObj != null)
            {
                mGroundTilemap = landBaseObj.GetComponent<Tilemap>();
            }

            StartCoroutine(InitializeManager());
        }
    }

    private IEnumerator InitializeManager()
    {
        // 한 프레임 대기하여 다른 오브젝트들의 Awake가 실행되도록 함
        yield return null;

        // ground tilemap 설정
        GameObject landBaseObj = GameObject.Find("Tilemap_land_base");
        if (landBaseObj != null)
        {
            mGroundTilemap = landBaseObj.GetComponent<Tilemap>();
        }

        mLocationTilemaps = new List<Tilemap>();
        mTileTree = new List<TileController>();

        // 씬의 모든 TileController 찾아서 등록
        var tileControllers = FindObjectsByType<TileController>(FindObjectsSortMode.None);
        foreach (var controller in tileControllers)
        {
            if (!mTileTree.Contains(controller))
            {
                mTileTree.Add(controller);
                mLocationTilemaps.Add(controller.Tilemap);
                if (mShowDebug)
                {
                    LogManager.Log("Env", $"TileManager: {controller.LocationName} 환경이 등록되었습니다.", 3);
                }
            }
        }

        // 초기화 완료 표시
        mIsInitialized = true;

        // 대기 중인 Target들 처리
        foreach (var target in mPendingTargets)
        {
            RegisterTarget(target);
        }
        mPendingTargets.Clear();
    }

    public void RegisterTarget(Interactable target)
    {
        // 초기화가 안 된 경우 대기 목록에 추가
        if (!mIsInitialized)
        {
            if (!mPendingTargets.Contains(target))
            {
                mPendingTargets.Add(target);
                if (mShowDebug)
                {
                    LogManager.Log("Env", $"TileManager: {target.name}을(를) 대기 목록에 추가했습니다.", 3);
                }
            }
            return;
        }

        // 초기화가 완료된 경우 바로 등록
        Vector3Int cellPos = mGroundTilemap.WorldToCell(target.transform.position);
        TileController tileController = GetTileController(cellPos);
        
        if (tileController != null)
        {
            string locationName = tileController.LocationName;

            // 이미 같은 위치에 등록되어 있으면 무시
            if (mInteractableLocations.ContainsKey(target) && mInteractableLocations[target] == locationName)
                return;

            tileController.AddChildInteractable(target);
            
            // 위치 정보 업데이트
            mInteractableLocations[target] = locationName;
            target.UpdateCurrentLocation(locationName);
            if (target.mInteractableData.mType != InteractableData.Types.Agent)
            {
                target.TargetController.UpdateStandingPoints();
            }
            
            if (mShowDebug)
            {
                LogManager.Log("Env", $"TileManager: {target.name}을(를) {locationName}에 등록했습니다.", 3);
            }
        }
        else
        {
            LogManager.Log("Env", $"TileManager: {target.name}의 위치에 해당하는 TileController를 찾을 수 없습니다.", 1);
        }
    }

    public void UnregisterTarget(Interactable target)
    {
        // 대기 목록에서 제거
        if (mPendingTargets.Contains(target))
        {
            mPendingTargets.Remove(target);
            if (mShowDebug)
            {
                LogManager.Log("Env", $"TileManager: {target.name}을(를) 대기 목록에서 제거했습니다.", 3);
            }
            return;
        }

        // 위치 정보에서 제거
        mInteractableLocations.Remove(target);

        // 모든 TileController에서 제거 시도
        bool removed = false;
        foreach (TileController tileController in TileTree)
        {
            if (tileController.RemoveChildInteractable(target))
            {
                removed = true;
                target.UpdateCurrentLocation(null); // 위치 정보 초기화
                if (mShowDebug)
                {
                    LogManager.Log("Env", $"TileManager: {target.name}을(를) {tileController.LocationName}에서 제거했습니다.", 3);
                }
            }
        }

        if (!removed && mShowDebug)
        {
            LogManager.Log("Env", $"TileManager: {target.name}이(가) 어떤 환경에도 등록되어 있지 않았습니다.", 3);
        }
    }

    // Interactable의 현재 위치 반환
    public string GetInteractableLocation(Interactable interactable)
    {
        return mInteractableLocations.TryGetValue(interactable, out string location) ? location : null;
    }

    // 특정 위치에 있는 모든 Interactable 반환
    public List<Interactable> GetInteractablesInLocation(string locationName)
    {
        return mInteractableLocations
            .Where(kvp => kvp.Value == locationName)
            .Select(kvp => kvp.Key)
            .ToList();
    }

    // 디버깅
    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            LogManager.Log("Env", $"타일맵트리", 2);
            foreach (var tileController in mTileTree)
            {
                LogManager.Log("Env", $"타일맵 : {tileController.LocationName}", 2);
                foreach (var childInteractable in tileController.ChildInteractables)
                {
                    LogManager.Log("Env", $"오브젝트 : {childInteractable.mInteractableData.mName}", 2);
                }
            }
        }
    }

    public Tilemap GroundTilemap { get { return mGroundTilemap; } }

    public LayerMask WallLayerMask { get { return mWallLayerMask; } }
    public LayerMask ObjectLayerMask { get { return mObjectLayerMask; } }
    public LayerMask ItemLayerMask { get { return mItemLayerMask; } }
    public LayerMask NPCLayerMask { get { return mNPCLayerMask; } }
    public LayerMask VisionLayerMask { get { return mVisionLayerMask; } }
    public LayerMask ObstacleLayerMask { get { return mWallLayerMask | mObjectLayerMask | mNPCLayerMask; } }
    public LayerMask InteractableLayerMask { get { return mObjectLayerMask | mItemLayerMask | mNPCLayerMask; } }
    public LayerMask AllLayerMask { get { return mWallLayerMask | mObjectLayerMask | mItemLayerMask | mNPCLayerMask; } }

    public List<TileController> TileTree { get { return mTileTree; } }

    public TileController GetTileController(Vector3Int position)
    {
        if (mShowDebug)
        {
            LogManager.Log("Env", $"TileManager: 위치 {position}에서 TileController 검색 중", 3);
            LogManager.Log("Env", $"등록된 Tilemap 수: {mLocationTilemaps.Count}", 3);
        }

        foreach (var locationTilemap in mLocationTilemaps)
        {
            if (mShowDebug)
            {
                LogManager.Log("Env", $"검사 중인 Tilemap: {locationTilemap.name}, HasTile: {locationTilemap.HasTile(position)}", 3);
            }

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
        foreach (var tileController in mTileTree)
        {
            if (tileController.LocationName == locationName)
            {
                return tileController;
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

    private void OnDestroy()
    {
        // 오브젝트가 파괴될 때 씬 로드 이벤트 해제
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }

    public void SaveData()
    {
        // 저장할 데이터 리스트 생성
        InteractableSaveDataList saveList = new InteractableSaveDataList();
        saveList.mList = new List<InteractableSaveData>();

        // mTileTree에 등록된 모든 Interactable 오브젝트 정보 수집
        foreach (var tileController in mTileTree)
        {
            foreach (var interactable in tileController.ChildInteractables)
            {
                InteractableSaveData data = new InteractableSaveData();

                // 프리팹 이름은 오브젝트 이름에서 ( 전까지 추출
                data.mPrefabName = interactable.gameObject.name.Split('(')[0].Trim();
                if (data.mPrefabName == "NPC") continue;

                data.mPosition = interactable.transform.position;
                saveList.mList.Add(data);
            }
        }

        // Json으로 직렬화
        string json = JsonUtility.ToJson(saveList, true);

        // 파일로 저장 (경로는 Application.persistentDataPath 사용해서 PC는 C:\Users\SSAFY\AppData\LocalLow\DefaultCompany\OhMaiGod 저장됨)
        string path = System.IO.Path.Combine(Application.persistentDataPath, "interactables.json");
        System.IO.File.WriteAllText(path, json);

        LogManager.Log("Env", $"Interactable 세이브 완료: {path}", 2);
    }

    public void LoadData()
    {
        // 저장된 데이터 파일 경로
        string path = System.IO.Path.Combine(Application.persistentDataPath, "interactables.json");
        if (!System.IO.File.Exists(path))
        {
            LogManager.Log("SaveLoad", "세이브 파일이 존재하지 않습니다.", 1);
            return;
        }

        // 파일에서 Json 읽기
        string json = System.IO.File.ReadAllText(path);
        InteractableSaveDataList saveList = JsonUtility.FromJson<InteractableSaveDataList>(json);
        if (saveList.mList == null)
        {
            LogManager.Log("SaveLoad", "세이브 데이터가 비어 있습니다.", 1);
            return;
        }

        // 기존 Target 태그 오브젝트 모두 삭제
        GameObject[] targetObjs = GameObject.FindGameObjectsWithTag("Target");
        foreach (var obj in targetObjs)
        {
            GameObject.Destroy(obj);
            LogManager.Log("SaveLoad", $"기존 Target 오브젝트({obj.name}) 삭제", 2);
        }

        // 저장된 데이터로 Interactable 오브젝트 생성
        foreach (InteractableSaveData data in saveList.mList)
        {
            // 프리팹 로드 (PrefabManager에서 프리팹 레퍼런스 가져와서 로드)
            GameObject prefab = PrefabManager.Instance.GetPrefabByName(data.mPrefabName);
            if (prefab == null)
            {
                LogManager.Log("SaveLoad", $"프리팹 {data.mPrefabName}을(를) 찾을 수 없습니다.", 1);
                continue;
            }

            // 오브젝트 생성 및 위치 지정
            Instantiate(prefab, data.mPosition, Quaternion.identity);
        }

        LogManager.Log("SaveLoad", "Interactable 오브젝트 로드 완료.", 2);
    }
}