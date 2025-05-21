using UnityEngine;
using UnityEngine.UI;
using TMPro;
public class ResourceUI : MonoBehaviour
{
    [SerializeField] private Inventory.ResourceType mResourceType;
    private TextMeshProUGUI mText;

    private void Start()
    {
        mText = GetComponent<TextMeshProUGUI>();
    }

    private void Update()
    {
        switch (mResourceType)
        {
            case Inventory.ResourceType.Wood:
                mText.text = string.Format("{0}", Inventory.Instance.ResourceItems.wood);
                break;
            case Inventory.ResourceType.Stone:
                mText.text = string.Format("{0}", Inventory.Instance.ResourceItems.stone);
                break;
            case Inventory.ResourceType.Power:
                mText.text = string.Format("{0}", Inventory.Instance.ResourceItems.power);
                break;
        }
    }
}
