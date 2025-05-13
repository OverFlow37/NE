using UnityEngine;
using System;

public class EffectController : MonoBehaviour
{
    [SerializeField]
    public GameObject mEffectObject;
    [SerializeField]
    private int mLifeDuration; // 이펙트 수명
    private TimeSpan mStartTime;

    private Animator mAnimator;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        mStartTime = TimeManager.Instance.GetCurrentGameTime();
        mAnimator = mEffectObject.GetComponent<Animator>();

        if (mAnimator != null)
        {
            // 애니메이션 클립 길이 구하기
            float animLength = mAnimator.runtimeAnimatorController.animationClips[0].length;
            // 속도 조절
            mAnimator.speed = animLength / mLifeDuration;
        }
    }

    void Update()
    {
        // 이벤트 수명 체크
        if (TimeManager.Instance.GetCurrentGameTime() - mStartTime > TimeSpan.FromSeconds(mLifeDuration))
        {
            Destroy(gameObject);
        }
    }
}
