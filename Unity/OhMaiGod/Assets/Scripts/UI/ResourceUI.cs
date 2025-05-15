using UnityEngine;
using UnityEngine.UI;

public class ResourceUI : MonoBehaviour
{
    [SerializeField] private Inventory.ResourceType mResourceType;
    private Text mText;

    private void Start()
    {
        mText = GetComponent<Text>();
    }

    private void Update()
    {
        switch (mResourceType)
        {
            case Inventory.ResourceType.Wood:
                mText.text = "WOOD  : " + string.Format("{0}", Inventory.Instance.ResourceItems.wood);
                break;
            case Inventory.ResourceType.Stone:
                mText.text = "STONE : " + string.Format("{0}", Inventory.Instance.ResourceItems.stone);
                break;
            case Inventory.ResourceType.Power:
                mText.text = "POWER : " + string.Format("{0}", Inventory.Instance.ResourceItems.power);
                break;
        }
    }
}
