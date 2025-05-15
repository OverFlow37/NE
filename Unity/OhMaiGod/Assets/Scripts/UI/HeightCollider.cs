using UnityEngine;

public class HeightCollider : MonoBehaviour
{
    [SerializeField, ReadOnly] private SpriteRenderer mSpriteRenderer;

    private void Awake()
    {
        mSpriteRenderer = GetComponentInParent<SpriteRenderer>();
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        Debug.Log("OnTriggerEnter2D: " + other.gameObject.name + ", layer: " + other.gameObject.layer);
        // LayerMask와 비교는 비트 연산으로 해야 함
        if (((1 << other.gameObject.layer) & TileManager.Instance.NPCLayerMask) != 0)
        {
            // HeightCollider(윗부분) 반투명
            if (mSpriteRenderer != null)
                mSpriteRenderer.color = new Color(1, 1, 1, 0.5f);

            // NPC 본체도 반투명
            var npcRenderer = other.GetComponent<SpriteRenderer>();
            if (npcRenderer != null)
                npcRenderer.color = new Color(1, 1, 1, 0.7f);
        }
    }

    private void OnTriggerExit2D(Collider2D other)
    {
        Debug.Log("OnTriggerExit2D: " + other.gameObject.name + ", layer: " + other.gameObject.layer);
        // LayerMask와 비교는 비트 연산으로 해야 함
        if (((1 << other.gameObject.layer) & TileManager.Instance.NPCLayerMask) != 0)
        {
            // HeightCollider(윗부분) 불투명
            if (mSpriteRenderer != null)
                mSpriteRenderer.color = new Color(1, 1, 1, 1);

            // NPC 본체도 불투명
            var npcRenderer = other.GetComponent<SpriteRenderer>();
            if (npcRenderer != null)
                npcRenderer.color = new Color(1, 1, 1, 1);
        }
    }
}
