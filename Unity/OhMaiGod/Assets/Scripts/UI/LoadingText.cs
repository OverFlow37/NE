using UnityEngine;
using TMPro;
using System.Collections;

public class LoadingText : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI loadingText;
    [SerializeField] private string baseText = "";
    [SerializeField] private float dotChangeInterval = 0.5f;
    
    private void Start()
    {
        // 할당된 텍스트가 없으면 현재 게임오브젝트에서 찾기
        if (loadingText != null)
        {
            StartCoroutine(AnimateDots());
        }
    }
    
    private IEnumerator AnimateDots()
    {
        int dotCount = 0;
        
        while (true)
        {
            switch (dotCount)
            {
                case 0:
                    loadingText.text = baseText;
                    break;
                case 1:
                    loadingText.text = baseText + ".";
                    break;
                case 2:
                    loadingText.text = baseText + "..";
                    break;
                case 3:
                    loadingText.text = baseText + "...";
                    break;
            }
            
            dotCount = (dotCount + 1) % 4;
            yield return new WaitForSeconds(dotChangeInterval);
        }
    }
}