using UnityEngine;

public class Power : MonoBehaviour
{
    [Header("버튼 컨트롤러")]
    [SerializeField] private ButtonController mButtonController; // ButtonController 참조
    private PowerManager mPowerManager;
    public int mPowerCost = 0;
    private void Start()
    {
        mPowerManager = GameObject.Find("PowerManager").GetComponent<PowerManager>();
    }
    protected bool mIsActive = false;
    public virtual void Active(){
        if(Inventory.Instance.ResourceItems.power < mPowerCost){
            return;
        }
        mPowerManager.DeactiveOtherPowers();
        mButtonController.IsOn();
        mIsActive = true;
    }
    public virtual void Deactive()
    {
        mButtonController.IsOFF();
        mIsActive = false;
    }
}
