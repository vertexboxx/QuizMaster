def create_quiz(client, title="Test Quiz", difficulty="easy", category="General"):
    response = client.post("/api/quizzes", json={
        "title": title,
        "difficulty": difficulty,
        "category": category,
    })
    return response.get_json()["id"]


def add_question(client, quiz_id, correct_option="B"):
    return client.post(f"/api/quizzes/{quiz_id}/questions", json={
        "text": "What is 1 + 1?",
        "option_a": "1",
        "option_b": "2",
        "option_c": "3",
        "option_d": "4",
        "correct_option": correct_option,
    })


def test_list_quizzes_empty(client):
    response = client.get("/api/quizzes")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_quiz(client):
    response = client.post("/api/quizzes", json={"title": "Maths"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Maths"
    assert data["difficulty"] == "easy"


def test_create_quiz_empty_title(client):
    response = client.post("/api/quizzes", json={"title": "  "})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_quiz_wrong_difficulty(client):
    response = client.post("/api/quizzes", json={
        "title": "Maths",
        "difficulty": "impossible",
    })
    assert response.status_code == 400


def test_filter_quizzes_by_difficulty(client):
    create_quiz(client, "Easy One", "easy")
    create_quiz(client, "Hard One", "hard")
    response = client.get("/api/quizzes?difficulty=hard")
    quizzes = response.get_json()
    assert len(quizzes) == 1
    assert quizzes[0]["title"] == "Hard One"


def test_sort_quizzes_by_title(client):
    create_quiz(client, "Zebra Quiz")
    create_quiz(client, "apple Quiz")
    create_quiz(client, "Mango Quiz")

    response = client.get("/api/quizzes?sort=title")

    assert response.status_code == 200
    titles = [quiz["title"] for quiz in response.get_json()]
    assert titles == ["apple Quiz", "Mango Quiz", "Zebra Quiz"]


def test_sort_quizzes_by_title_desc(client):
    create_quiz(client, "Apple Quiz")
    create_quiz(client, "Mango Quiz")
    create_quiz(client, "Zebra Quiz")

    response = client.get("/api/quizzes?sort=title&order=desc")

    titles = [quiz["title"] for quiz in response.get_json()]
    assert titles == ["Zebra Quiz", "Mango Quiz", "Apple Quiz"]


def test_sort_quizzes_by_difficulty(client):
    create_quiz(client, "Hard Quiz", "hard")
    create_quiz(client, "Easy Quiz", "easy")
    create_quiz(client, "Medium Quiz", "medium")

    response = client.get("/api/quizzes?sort=difficulty")

    titles = [quiz["title"] for quiz in response.get_json()]
    assert titles == ["Easy Quiz", "Medium Quiz", "Hard Quiz"]


def test_sort_quizzes_by_difficulty_desc(client):
    create_quiz(client, "Easy Quiz", "easy")
    create_quiz(client, "Hard Quiz", "hard")
    create_quiz(client, "Medium Quiz", "medium")

    response = client.get("/api/quizzes?sort=difficulty&order=desc")

    titles = [quiz["title"] for quiz in response.get_json()]
    assert titles == ["Hard Quiz", "Medium Quiz", "Easy Quiz"]


def test_sort_quizzes_by_created_at(client):
    create_quiz(client, "First Quiz")
    create_quiz(client, "Second Quiz")
    create_quiz(client, "Third Quiz")

    response = client.get("/api/quizzes?sort=created_at")

    titles = [quiz["title"] for quiz in response.get_json()]
    assert titles == ["First Quiz", "Second Quiz", "Third Quiz"]


def test_sort_quizzes_invalid_sort(client):
    response = client.get("/api/quizzes?sort=invalid")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_sort_quizzes_invalid_order(client):
    response = client.get("/api/quizzes?sort=title&order=random")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_list_quizzes_default_order(client):
    create_quiz(client, "First Quiz")
    create_quiz(client, "Second Quiz")
    create_quiz(client, "Third Quiz")

    response = client.get("/api/quizzes")

    titles = [quiz["title"] for quiz in response.get_json()]
    assert titles == ["First Quiz", "Second Quiz", "Third Quiz"]



def test_get_quiz_not_found(client):
    response = client.get("/api/quizzes/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Quiz not found"}


def test_get_quiz_hides_correct_answers(client):
    quiz_id = create_quiz(client)
    add_question(client, quiz_id)
    response = client.get(f"/api/quizzes/{quiz_id}")
    questions = response.get_json()["questions"]
    assert len(questions) == 1
    assert "correct_option" not in questions[0]


def test_add_question(client):
    quiz_id = create_quiz(client)
    response = add_question(client, quiz_id)
    assert response.status_code == 201
    assert response.get_json()["text"] == "What is 1 + 1?"


def test_add_question_wrong_option_letter(client):
    quiz_id = create_quiz(client)
    response = add_question(client, quiz_id, correct_option="E")
    assert response.status_code == 400


def test_add_question_quiz_not_found(client):
    response = add_question(client, 999)
    assert response.status_code == 404


def test_submit_quiz_scores_answers(client):
    quiz_id = create_quiz(client)
    add_question(client, quiz_id, "B")
    question_id = client.get(f"/api/quizzes/{quiz_id}").get_json()["questions"][0]["id"]

    response = client.post(f"/api/quizzes/{quiz_id}/submit", json={
        "player_name": "Asha",
        "answers": {str(question_id): "B"},
        "time_taken_seconds": 12,
    })
    assert response.status_code == 200
    result = response.get_json()
    assert result["score"] == 1
    assert result["wrong"] == 0
    assert result["time_taken_seconds"] == 12


def test_submit_quiz_missing_player_name(client):
    quiz_id = create_quiz(client)
    add_question(client, quiz_id)
    response = client.post(f"/api/quizzes/{quiz_id}/submit", json={"answers": {}})
    assert response.status_code == 400


def test_submit_quiz_not_found(client):
    response = client.post("/api/quizzes/999/submit", json={
        "player_name": "Asha",
        "answers": {},
    })
    assert response.status_code == 404


def test_leaderboard_is_sorted_and_limited(client):
    quiz_id = create_quiz(client)
    add_question(client, quiz_id, "B")
    question_id = client.get(f"/api/quizzes/{quiz_id}").get_json()["questions"][0]["id"]
    for i in range(12):
        # Even numbered players answer correctly
        answer = "B" if i % 2 == 0 else "A"
        client.post(f"/api/quizzes/{quiz_id}/submit", json={
            "player_name": f"Player {i}",
            "answers": {str(question_id): answer},
        })

    response = client.get(f"/api/quizzes/{quiz_id}/leaderboard")
    entries = response.get_json()
    assert len(entries) == 10
    assert entries[0]["score"] == 1
    assert entries[-1]["score"] == 0


def test_stats(client):
    quiz_id = create_quiz(client)
    add_question(client, quiz_id, "B")
    question_id = client.get(f"/api/quizzes/{quiz_id}").get_json()["questions"][0]["id"]
    client.post(f"/api/quizzes/{quiz_id}/submit", json={
        "player_name": "Asha",
        "answers": {str(question_id): "B"},
    })

    stats = client.get("/api/stats").get_json()
    assert stats["total_quizzes"] == 1
    assert stats["total_attempts"] == 1
    assert stats["quizzes"][0]["average_score"] == 1


