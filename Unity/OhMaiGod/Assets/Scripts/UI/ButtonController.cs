using UnityEngine;
using UnityEngine.UI;

public class ButtonController : MonoBehaviour
{
    [SerializeField] private Image mButtonBackgroundImage; // 버튼의 Image 컴포넌트
    [SerializeField] private Sprite mSpriteOn;   // 토글 ON 스프라이트
    [SerializeField] private Sprite mSpriteOff;  // 토글 OFF 스프라이트
    private bool mIsOn = false;


    public void IsOn()
    {
        mButtonBackgroundImage.sprite = mSpriteOn;
    }
    public void IsOFF()
    {
        mButtonBackgroundImage.sprite = mSpriteOff;
    }
}
