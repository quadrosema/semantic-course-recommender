from flask import Flask, jsonify, request
from day2.recommendation_pipeline import recommend_for_user
from day3.workflow import recommend_with_workflow


app = Flask(__name__)


@app.post("/api/recommend")
def recommend():
    """Return recommendations for either a stored user or free-form user text."""
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"detail": "Request body must be a JSON object."}), 400

    user_id = payload.get("user_id")
    user_text = payload.get("user_text", "")
    top_n = payload.get("top_n", 3)

    if not isinstance(user_text, str):
        return jsonify({"detail": "`user_text` must be a string."}), 400

    user_text = user_text.strip()

    if (
        isinstance(top_n, bool)
        or not isinstance(top_n, int)
        or not 1 <= top_n <= 10
    ):
        return jsonify(
            {"detail": "`top_n` must be an integer from 1 to 10."}
        ), 400

    if user_id is None and not user_text:
        return jsonify(
            {"detail": "Provide either `user_id` or `user_text."}
        ), 400

    if user_id is not None and user_text:
        return jsonify(
            {"detail": "Provide only one of `user_id` or `user_text."}
        ), 400

    if user_id is not None:
        if (
            isinstance(user_id, bool)
            or not isinstance(user_id, int)
            or user_id < 1
        ):
            return jsonify(
                {"detail": "`user_id` must be a positive integer."}
            ), 400

        try:
            return jsonify(
                recommend_for_user(
                    user_id,
                    top_n=top_n,
                )
            )
        except ValueError as error:
            return jsonify({"detail": str(error)}), 404

    # Day 3: free-text recommendation workflow
    result = recommend_with_workflow(
        user_text=user_text,
        top_n=top_n,
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)

