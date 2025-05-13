using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System;
using System.Linq;
using OhMAIGod.Agent;
using Unity.VisualScripting;
using OhMAIGod.Perceive;

// 관찰 정보 AI로 전송
// 임계치에 따라 반응 판단과 관찰 정보 전송으로 나뉨
// find로 시작할때 agentController에서 연결할것
public class AIBridge_Perceive : MonoBehaviour
{    
    private bool mIsRequesting = false;

    // Interactable 목록을 ObjectGroup 배열로 변환
    private ObjectGroup[] ConvertToObjectGroups(List<Interactable> interactables)
    {
        // 위치별로 오브젝트들을 그룹화
        Dictionary<string, List<string>> locationGroups = new Dictionary<string, List<string>>();

        foreach (Interactable interactable in interactables)
        {
            if (interactable == null || interactable.mInteractableData == null) continue;

            string location = interactable.CurrentLocation;
            if (string.IsNullOrEmpty(location)) continue;

            if (!locationGroups.ContainsKey(location))
            {
                locationGroups[location] = new List<string>();
            }
            locationGroups[location].Add(interactable.InteractableName);
        }

        // Dictionary를 ObjectGroup 배열로 변환
        return locationGroups.Select(group => new ObjectGroup
        {
            location = group.Key,
            objects = group.Value
        }).ToArray();
    }
    
    // 관찰 이벤트 전송(응답없음)
    public void SendPerceiveEvent(AgentController agent, PerceiveEvent perceiveEvent)
    {
        StartCoroutine(SendPerceiveEventData(agent, perceiveEvent));
    }

    IEnumerator SendPerceiveEventData(AgentController agent, PerceiveEvent perceiveEvent){
        mIsRequesting = true;

        // ---- 에이전트 정보 ----
        // 현재 에이전트의 상태 정보 가져오기
        AgentNeeds currentNeeds = agent.AgnetNeeds;
        var movement = agent.mMovement;
        var scheduler = agent.mScheduler;

        // AI 서버에 보낼 요청 데이터 생성
        var visibleObjectGroups = ConvertToObjectGroups(agent.mVisibleInteractables);

        // 에이전트의 현재 위치 가져오기 (CurrentAction이 null일 경우 대비)
        string agentLocation = "Unknown"; // 기본값
        Interactable agentInteractable = agent.GetComponent<Interactable>();
        if (agentInteractable != null && !string.IsNullOrEmpty(agentInteractable.CurrentLocation))
        {
            agentLocation = agentInteractable.CurrentLocation;
        }
        else if (agent.CurrentAction != null && !string.IsNullOrEmpty(agent.CurrentAction.LocationName))
        {
            // CurrentAction이 있고 LocationName이 유효하면 해당 위치 사용
            agentLocation = agent.CurrentAction.LocationName;
        }

        for (int i = 0; i < visibleObjectGroups.Length; i++)
        {
            LogManager.Log("AI", $"[AIBridge_Perceive] ObjectGroup {i}: location={visibleObjectGroups[i].location}, objects=[{string.Join(",", visibleObjectGroups[i].objects)}]", 3);
        }

        AgentRequest requestData = new AgentRequest
        {
            agent = new Agent
            {
                name = agent.AgentName,
                state = currentNeeds,
                location = agentLocation,
                personality = "friendly, helpful", // TODO: 에이전트별 성격 구현 필요
                visible_objects = visibleObjectGroups
            }
        };
        // ---- 이벤트 정보 ----
        // perceiveEvent를 JSON으로 변환
        string eventJson = JsonUtility.ToJson(perceiveEvent);
        LogManager.Log("AI", $"[AIBridge_Perceive] perceiveEvent JSON: {eventJson}", 3);

        // HTTP 요청 설정 (임시 주소)
        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:5000/perceive", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(eventJson);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        mIsRequesting = false;

        if (request.result == UnityWebRequest.Result.Success)
        {
            LogManager.Log("AI", $"✅ perceiveEvent 전송 성공: " + request.downloadHandler.text, 2);
        }
        else
        {
            LogManager.Log("AI", $"❌ perceiveEvent 전송 실패: " + request.error, 0);
        }
    }

} 