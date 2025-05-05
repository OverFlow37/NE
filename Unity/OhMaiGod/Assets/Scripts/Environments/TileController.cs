using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

public class TileController : MonoBehaviour
{
    private string mLocationName;
    private List<TargetController> mChildInteractables;
    private bool mIsInitialized = false;
    private Tilemap mTilemap;

    private void Awake()
    {
        mTilemap = GetComponent<Tilemap>();
        mLocationName = mTilemap.name;
        mChildInteractables = new List<TargetController>();
    }

    private void Update()
    {
        if (!TileManager.Instance.mIsInitialized) return;
        if (!mIsInitialized)
        {
            TileManager.Instance.AddLocationTilemap(this);
            mIsInitialized = true;
        }
    }

    public Tilemap Tilemap { get { return mTilemap; } }
    public string LocationName { get { return mLocationName; } }
    public List<TargetController> ChildInteractables { get { return mChildInteractables; } }

    public void AddChildInteractable(TargetController interactable)
    {
        if (!mChildInteractables.Contains(interactable))
        {
            mChildInteractables.Add(interactable);
        }
    }

    public void RemoveChildInteractable(TargetController interactable)
    {
        if (mChildInteractables.Contains(interactable))
        {
            mChildInteractables.Remove(interactable);
        }
    }

    public void RemoveAllChildInteractables()
    {
        mChildInteractables.Clear();
    }
}
