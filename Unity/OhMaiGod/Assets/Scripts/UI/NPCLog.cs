using UnityEngine;
using UnityEngine.UI;

public class NPCLog : MonoBehaviour
{
    private Text mText;

    private void Start()
    {
        mText = GetComponent<Text>();
        mText.text = "";
    }

    public void SetNPCLog(string _text)
    {
        mText.text = _text;
    }
}
