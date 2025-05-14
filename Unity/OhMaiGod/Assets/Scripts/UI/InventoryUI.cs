using UnityEngine;
using UnityEngine.UI;

public class InventoryUI : MonoBehaviour
{
    public Inventory inventory;
    public Text inventoryText;

    void Update()
    {
        if (inventory != null && inventoryText != null)
        {
            inventoryText.text = inventory.GetInventoryString();
        }
    }
}
