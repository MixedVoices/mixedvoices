def process_vapi_webhook(webhook_data):
    message_data = webhook_data["message"]
    return {
        "source": "vapi",
        "call_info": {
            "messages": message_data["messages"],
            "transcript": message_data["transcript"],
            "stereo_recording_url": message_data["stereoRecordingUrl"],
            "recording_url": message_data["recordingUrl"],
            "started_at": message_data["startedAt"],
            "ended_at": message_data["endedAt"],
            "call_duration_seconds": message_data["durationSeconds"],
        },
        "analysis_info": {
            "summary": message_data["analysis"]["summary"],
            "success_evaluation": message_data["analysis"]["successEvaluation"],
            "ended_reason": message_data["endedReason"],
        },
        "id_info": {
            "call_id": message_data["call"]["id"],
            "org_id": message_data["call"]["orgId"],
        },
        "assistant_info": {
            "assistant_id": message_data["assistant"]["id"],
            "assistant_model": message_data["assistant"]["model"],
            "assistant_name": message_data["assistant"]["name"],
            "assistant_voice": message_data["assistant"]["voice"],
            "assistant_transcriber": message_data["assistant"]["transcriber"],
            "assistant_updated_at": message_data["assistant"]["updatedAt"],
        },
        "cost_info": {
            "call_cost": message_data["cost"],
            "cost_breakdown": message_data["costBreakdown"],
        },
    }
