using UnityEngine;

public class SoundEffectController : MonoBehaviour
{
    private AudioSource mAudioSource;
    private bool mIsPlayed = false;

    [Range(0f, 1f)]
    public float mVolume = 1.0f;

    void Start()
    {
        mAudioSource = GetComponent<AudioSource>();
        if (mAudioSource == null)
        {
            LogManager.Log("Sound", "AudioSource 컴포넌트를 찾을 수 없습니다.", 0);
            Destroy(gameObject);
            return;
        }
        mAudioSource.volume = mVolume;
        mAudioSource.Play();
        mIsPlayed = true;
        LogManager.Log("효과음 재생 시작");
    }

    void Update()
    {
        if (mIsPlayed && !mAudioSource.isPlaying)
        {
            LogManager.Log("효과음 재생 완료, 오브젝트 삭제");
            Destroy(gameObject);
        }
    }
}
