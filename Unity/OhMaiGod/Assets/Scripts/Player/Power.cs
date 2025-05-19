using UnityEngine;

public class Power : MonoBehaviour
{
    [Header("버튼 컨트롤러")]
    [SerializeField] private ButtonController mButtonController; // ButtonController 참조
    private PowerManager mPowerManager;
    private void Start()
    {
        mPowerManager = GameObject.Find("PowerManager").GetComponent<PowerManager>();
    }
    protected bool mIsActive = false;
    public virtual void Active(){
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
