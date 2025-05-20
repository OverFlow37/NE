using UnityEngine;
using System;

public class EffectController : MonoBehaviour
{
    [SerializeField]
    public GameObject mEffectObject;
    [SerializeField]
    private float mLifeDuration; // 이펙트 수명(초)
    [SerializeField]
    private float mStopBeforeDestroy = 1f; // 삭제 몇 초 전에 파티클 정지할지

    private Animator mAnimator;
    private ParticleSystem mParticleSystem;

    private TimeSpan mStartTime;
    private bool mParticleStopped = false;

    // Start is called once before the first execution of Update after the MonoBehaviour is created

    void Start()
    {
        if (mEffectObject == null)
        {
            LogManager.Log("Effect", "mEffectObject가 할당되지 않아 자동으로 자기 자신을 할당합니다.");
            mEffectObject = gameObject;
        }
        mStartTime = TimeManager.Instance.GetCurrentGameTime();
        if (mEffectObject.GetComponent<Animator>() != null)
        {
            mAnimator = mEffectObject.GetComponent<Animator>();
        }
        if (mEffectObject.GetComponent<ParticleSystem>() != null)
        {
            mParticleSystem = mEffectObject.GetComponent<ParticleSystem>();
        }
    }

    void Update()
    {
        TimeSpan elapsed = TimeManager.Instance.GetCurrentGameTime() - mStartTime;
        // 파티클 정지 시점 체크 (이펙트 수명 - mStopBeforeDestroy)
        if (mParticleSystem != null && !mParticleStopped && elapsed > TimeSpan.FromSeconds(mLifeDuration - mStopBeforeDestroy))
        {
            if (mParticleSystem.isPlaying)
            {
                LogManager.Log("Effect", "파티클 정지");
                mParticleSystem.Stop();
                mParticleStopped = true;
            }
        }
        // 이펙트 수명 체크
        if (elapsed > TimeSpan.FromSeconds(mLifeDuration))
        {
            Destroy(gameObject);
        }
    }
}
