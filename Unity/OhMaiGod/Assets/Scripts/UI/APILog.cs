using UnityEngine;
using UnityEngine.UI;

public class APILog : MonoBehaviour
{
    private Text mText;

    private void Start()
    {
        mText = GetComponent<Text>();
        mText.text = "";
    }

    public void SetAPILog(string _text)
    {
        mText.text = _text;
    }
}
