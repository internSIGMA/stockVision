"""
Flask Blueprint for Forecasting & Clustering API routes.
Provides clean REST API endpoints for the dashboard and UI/UX team.
"""

from flask import Blueprint, jsonify, request
import threading
from .database import (
    ensure_forecast_tables,
    load_cluster_assignments_full,
    load_cluster_metadata,
    load_cluster_members,
    load_all_hyperparams,
    load_cluster_hyperparams,
    load_accuracy_by_symbol,
    load_accuracy_summary,
    load_accuracy_dashboard,
    load_stock_data
)
from .clustering import run_clustering, assign_new_stock
from .hyperparameter_tuner import tune_all_clusters
from .pipeline import run_pipeline, run_clustering_pipeline, run_tuning_pipeline

forecast_bp = Blueprint("forecast_bp", __name__)


# Global status for asynchronous execution
_pipeline_status = {
    "is_running": False,
    "last_run": None,
    "last_status": None,
    "message": "Idle"
}


@forecast_bp.route("/api/forecast/clusters", methods=["GET"])
def get_clusters():
    """
    Returns list of all clusters with their metadata, centroids, silhouette score,
    and member symbols.
    """
    try:
        ensure_forecast_tables()
        metadata = load_cluster_metadata()
        assignments = load_cluster_assignments_full()

        # Group symbols by cluster_id
        cluster_groups = {}
        for row in assignments:
            cid = row["cluster_id"]
            if cid not in cluster_groups:
                cluster_groups[cid] = []
            cluster_groups[cid].append(row)

        result = []
        for meta in metadata:
            cid = meta["cluster_id"]
            members = cluster_groups.get(cid, [])
            result.append({
                "cluster_id": cid,
                "cluster_label": meta.get("cluster_label"),
                "n_members": meta.get("n_members", len(members)),
                "silhouette_score": meta.get("silhouette_score"),
                "centroids": {
                    "return": meta.get("centroid_return"),
                    "volatility": meta.get("centroid_volatility"),
                    "volume": meta.get("centroid_volume"),
                    "momentum": meta.get("centroid_momentum"),
                },
                "updated_at": str(meta.get("updated_at")),
                "members": members
            })

        return jsonify({
            "status": "success",
            "count": len(result),
            "data": result
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@forecast_bp.route("/api/forecast/cluster/<symbol>", methods=["GET"])
def get_stock_cluster(symbol):
    """
    Returns the cluster assignment and movement characteristics of a single emiten.
    """
    try:
        symbol = symbol.upper().strip()
        assignments = load_cluster_assignments_full()
        match = next((item for item in assignments if item["symbol"] == symbol), None)

        if not match:
            return jsonify({
                "status": "not_found",
                "message": f"Stock {symbol} has not been assigned to a cluster yet."
            }), 404

        metadata = load_cluster_metadata()
        meta = next((m for m in metadata if m["cluster_id"] == match["cluster_id"]), {})

        return jsonify({
            "status": "success",
            "data": {
                "symbol": match["symbol"],
                "cluster_id": match["cluster_id"],
                "cluster_label": match.get("cluster_label"),
                "avg_return": match.get("avg_return"),
                "avg_volatility": match.get("avg_volatility"),
                "avg_volume": match.get("avg_volume"),
                "momentum_score": match.get("momentum_score"),
                "updated_at": str(match.get("updated_at")),
                "cluster_summary": meta
            }
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@forecast_bp.route("/api/forecast/assign-stock", methods=["POST"])
def assign_single_stock():
    """
    Assigns a new or specified stock to the nearest cluster.
    Request JSON: {"symbol": "GOTO"}
    """
    try:
        data = request.get_json(silent=True) or {}
        symbol = data.get("symbol", "").upper().strip()
        if not symbol:
            return jsonify({"status": "error", "message": "Missing 'symbol' parameter."}), 400

        df = load_stock_data()
        stock_df = df[df["symbol"] == symbol]
        if stock_df.empty:
            return jsonify({
                "status": "error",
                "message": f"No OHLC data found for symbol {symbol} to calculate features."
            }), 404

        cluster_id = assign_new_stock(symbol, stock_df)
        return jsonify({
            "status": "success",
            "symbol": symbol,
            "assigned_cluster_id": cluster_id,
            "message": f"Symbol {symbol} assigned to cluster {cluster_id}."
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@forecast_bp.route("/api/forecast/hyperparams", methods=["GET"])
def get_hyperparams():
    """
    Returns all tuned hyperparameters per cluster.
    """
    try:
        params = load_all_hyperparams()
        return jsonify({
            "status": "success",
            "count": len(params),
            "data": params
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@forecast_bp.route("/api/forecast/accuracy", methods=["GET"])
def get_accuracy():
    """
    Returns accuracy metrics.
    Query param: ?symbol=BBCA (optional)
    """
    try:
        symbol = request.args.get("symbol")
        if symbol:
            symbol = symbol.upper().strip()
            records = load_accuracy_by_symbol(symbol)
            return jsonify({
                "status": "success",
                "symbol": symbol,
                "count": len(records),
                "data": records
            }), 200
        else:
            summary = load_accuracy_summary()
            return jsonify({
                "status": "success",
                "count": len(summary),
                "data": summary
            }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@forecast_bp.route("/api/forecast/accuracy/summary", methods=["GET"])
def get_accuracy_summary():
    """
    Returns average accuracy metrics grouped by cluster and target.
    """
    try:
        summary = load_accuracy_summary()
        return jsonify({
            "status": "success",
            "count": len(summary),
            "data": summary
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@forecast_bp.route("/api/forecast/accuracy/dashboard", methods=["GET"])
def get_accuracy_dashboard():
    """
    Main endpoint for frontend dashboard:
    Returns symbol list with cluster metadata, target prediction accuracy %, confidence label, MAE, RMSE, MAPE, R2.
    """
    try:
        dashboard_data = load_accuracy_dashboard()
        return jsonify({
            "status": "success",
            "count": len(dashboard_data),
            "data": dashboard_data
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@forecast_bp.route("/api/forecast/run-clustering", methods=["POST"])
def trigger_clustering():
    """
    Triggers K-Means clustering across all stocks.
    Request JSON (optional): {"n_clusters": "auto" | 5}
    """
    try:
        data = request.get_json(silent=True) or {}
        n_clusters = data.get("n_clusters", "auto")
        
        assignments, metadata, _ = run_clustering_pipeline(n_clusters=n_clusters)
        return jsonify({
            "status": "success",
            "message": f"Clustering completed with {len(metadata)} clusters across {len(assignments)} stocks.",
            "clusters": metadata
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@forecast_bp.route("/api/forecast/run-tuning", methods=["POST"])
def trigger_tuning():
    """
    Triggers Optuna hyperparameter tuning across clusters.
    Request JSON (optional): {"n_trials": 20}
    """
    try:
        data = request.get_json(silent=True) or {}
        n_trials = data.get("n_trials", None)
        
        results = run_tuning_pipeline(n_trials=n_trials)
        return jsonify({
            "status": "success",
            "message": f"Hyperparameter tuning completed for {len(results)} cluster-target pairs.",
            "results": results
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@forecast_bp.route("/api/forecast/run-pipeline", methods=["POST"])
def trigger_pipeline():
    """
    Triggers the end-to-end forecasting pipeline in a background thread or synchronously.
    Query param / JSON:
      - async: true/false (default true)
      - force_recluster: true/false (default false)
      - run_tuning: true/false (default false)
      - n_trials: integer (optional)
    """
    global _pipeline_status
    if _pipeline_status["is_running"]:
        return jsonify({
            "status": "busy",
            "message": "Pipeline is already running in background.",
            "current_status": _pipeline_status
        }), 409

    data = request.get_json(silent=True) or {}
    is_async = data.get("async", True)
    force_recluster = data.get("force_recluster", False)
    run_tuning = data.get("run_tuning", False)
    n_trials = data.get("n_trials", None)

    def worker():
        global _pipeline_status
        _pipeline_status["is_running"] = True
        _pipeline_status["message"] = "Pipeline executing..."
        try:
            success = run_pipeline(
                force_recluster=force_recluster,
                run_tuning=run_tuning,
                n_trials=n_trials
            )
            _pipeline_status["last_status"] = "success" if success else "failed"
            _pipeline_status["message"] = "Pipeline finished successfully." if success else "Pipeline failed."
        except Exception as err:
            _pipeline_status["last_status"] = "error"
            _pipeline_status["message"] = f"Error: {err}"
        finally:
            import datetime
            _pipeline_status["is_running"] = False
            _pipeline_status["last_run"] = datetime.datetime.now().isoformat()

    if is_async:
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        return jsonify({
            "status": "accepted",
            "message": "Forecasting pipeline started in background."
        }), 202
    else:
        worker()
        return jsonify({
            "status": _pipeline_status["last_status"],
            "message": _pipeline_status["message"]
        }), 200


@forecast_bp.route("/api/forecast/pipeline-status", methods=["GET"])
def get_pipeline_status():
    """
    Returns the current execution status of background pipeline jobs.
    """
    return jsonify({
        "status": "success",
        "data": _pipeline_status
    }), 200
