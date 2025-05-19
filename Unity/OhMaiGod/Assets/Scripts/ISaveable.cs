using UnityEngine;


// 저장 및 로드가 필요한 클래스가 반드시 구현해야 하는 인터페이스.
public interface ISaveable
{
    // 데이터를 저장하는 함수.
    public void SaveData(string _savePath);

    // 데이터를 로드하는 함수.
    public void LoadData(string _loadPath);
}
