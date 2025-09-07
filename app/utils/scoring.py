"""
Confidence scoring and evaluation utilities.

This module provides functions to compute confidence scores and
evaluate the quality of model predictions and results.
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple
import statistics

logger = logging.getLogger(__name__)


def compute_confidence(prediction: Dict[str, Any]) -> float:
    """
    Compute an adjusted confidence score for model predictions.
    
    This function takes raw model predictions and computes a more
    reliable confidence score based on various factors.
    
    Args:
        prediction: Dictionary containing prediction results with 'score' or similar
        
    Returns:
        float: Adjusted confidence score between 0.0 and 1.0
        
    Raises:
        ValueError: If prediction is empty or invalid
    """
    try:
        if not prediction:
            raise ValueError("Prediction dictionary cannot be empty")
        
        # Extract base confidence score
        base_score = prediction.get('score', prediction.get('confidence', 0.0))
        
        if not isinstance(base_score, (int, float)):
            logger.warning(f"Invalid confidence score type: {type(base_score)}")
            return 0.0
        
        # Ensure score is between 0 and 1
        base_score = max(0.0, min(1.0, float(base_score)))
        
        # Apply adjustments based on prediction characteristics
        adjusted_score = base_score
        
        # Adjust based on prediction margin (if available)
        if 'margin' in prediction:
            margin = prediction['margin']
            if margin > 0.5:  # High margin increases confidence
                adjusted_score = min(1.0, adjusted_score * 1.1)
            elif margin < 0.2:  # Low margin decreases confidence
                adjusted_score = adjusted_score * 0.9
        
        # Adjust based on model certainty indicators
        if 'entropy' in prediction:
            entropy = prediction['entropy']
            # Lower entropy means higher certainty
            entropy_factor = 1 - min(1.0, entropy / 2.0)  # Normalize entropy
            adjusted_score = adjusted_score * (0.8 + 0.2 * entropy_factor)
        
        # Adjust based on input quality indicators
        if 'input_quality' in prediction:
            quality = prediction['input_quality']
            if quality < 0.5:  # Poor input quality reduces confidence
                adjusted_score = adjusted_score * (0.5 + quality)
        
        # Apply sigmoid smoothing to avoid extreme values
        adjusted_score = _sigmoid_smooth(adjusted_score)
        
        return round(adjusted_score, 4)
        
    except Exception as e:
        logger.error(f"Confidence computation failed: {str(e)}")
        return 0.0


def _sigmoid_smooth(score: float, steepness: float = 10.0) -> float:
    """
    Apply sigmoid smoothing to confidence scores.
    
    Args:
        score: Input score
        steepness: Steepness of the sigmoid curve
        
    Returns:
        float: Smoothed score
    """
    try:
        # Shift score to center around 0.5
        centered = (score - 0.5) * steepness
        return 1.0 / (1.0 + math.exp(-centered))
    except (OverflowError, ZeroDivisionError):
        return score


def compute_ensemble_confidence(predictions: List[Dict[str, Any]]) -> float:
    """
    Compute confidence score from ensemble of predictions.
    
    Args:
        predictions: List of prediction dictionaries
        
    Returns:
        float: Ensemble confidence score
    """
    try:
        if not predictions:
            return 0.0
        
        confidences = []
        for pred in predictions:
            conf = compute_confidence(pred)
            confidences.append(conf)
        
        if not confidences:
            return 0.0
        
        # Use weighted average based on individual confidences
        weights = [conf for conf in confidences]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return 0.0
        
        weighted_confidence = sum(conf * weight for conf, weight in zip(confidences, weights)) / total_weight
        
        # Apply agreement bonus if predictions agree
        agreement_bonus = _calculate_agreement_bonus(predictions)
        final_confidence = min(1.0, weighted_confidence * (1 + agreement_bonus))
        
        return round(final_confidence, 4)
        
    except Exception as e:
        logger.error(f"Ensemble confidence computation failed: {str(e)}")
        return 0.0


def _calculate_agreement_bonus(predictions: List[Dict[str, Any]]) -> float:
    """
    Calculate bonus based on agreement between predictions.
    
    Args:
        predictions: List of predictions
        
    Returns:
        float: Agreement bonus factor (0.0 to 0.2)
    """
    try:
        if len(predictions) < 2:
            return 0.0
        
        # For classification, check if labels agree
        labels = []
        for pred in predictions:
            label = pred.get('label', pred.get('category', pred.get('class', None)))
            if label:
                labels.append(label)
        
        if len(labels) >= 2:
            # Calculate agreement percentage
            most_common = max(set(labels), key=labels.count)
            agreement_rate = labels.count(most_common) / len(labels)
            
            # Convert to bonus (max 20% bonus for full agreement)
            return (agreement_rate - 1/len(labels)) * 0.2
        
        return 0.0
        
    except Exception:
        return 0.0


def evaluate_search_results(
    results: List[Dict[str, Any]],
    relevance_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Evaluate the quality of search results.
    
    Args:
        results: List of search result dictionaries with similarity scores
        relevance_threshold: Minimum similarity score to consider relevant
        
    Returns:
        Dict[str, Any]: Evaluation metrics
    """
    try:
        if not results:
            return {
                "total_results": 0,
                "relevant_results": 0,
                "average_similarity": 0.0,
                "precision_at_5": 0.0,
                "precision_at_10": 0.0
            }
        
        similarities = []
        relevant_count = 0
        
        for result in results:
            similarity = result.get('similarity', result.get('score', 0.0))
            similarities.append(similarity)
            
            if similarity >= relevance_threshold:
                relevant_count += 1
        
        total_results = len(results)
        avg_similarity = statistics.mean(similarities) if similarities else 0.0
        
        # Calculate precision at different cutoffs
        precision_at_5 = _calculate_precision_at_k(results, relevance_threshold, 5)
        precision_at_10 = _calculate_precision_at_k(results, relevance_threshold, 10)
        
        return {
            "total_results": total_results,
            "relevant_results": relevant_count,
            "relevance_rate": round(relevant_count / total_results, 4),
            "average_similarity": round(avg_similarity, 4),
            "median_similarity": round(statistics.median(similarities), 4),
            "precision_at_5": round(precision_at_5, 4),
            "precision_at_10": round(precision_at_10, 4),
            "score_distribution": _calculate_score_distribution(similarities)
        }
        
    except Exception as e:
        logger.error(f"Search results evaluation failed: {str(e)}")
        return {"error": str(e)}


def _calculate_precision_at_k(
    results: List[Dict[str, Any]],
    threshold: float,
    k: int
) -> float:
    """
    Calculate precision at k for search results.
    
    Args:
        results: Search results
        threshold: Relevance threshold
        k: Number of top results to consider
        
    Returns:
        float: Precision at k
    """
    try:
        if not results or k <= 0:
            return 0.0
        
        top_k = results[:k]
        relevant_in_top_k = 0
        
        for result in top_k:
            similarity = result.get('similarity', result.get('score', 0.0))
            if similarity >= threshold:
                relevant_in_top_k += 1
        
        return relevant_in_top_k / len(top_k)
        
    except Exception:
        return 0.0


def _calculate_score_distribution(scores: List[float]) -> Dict[str, float]:
    """
    Calculate distribution of scores.
    
    Args:
        scores: List of similarity/confidence scores
        
    Returns:
        Dict[str, float]: Score distribution statistics
    """
    try:
        if not scores:
            return {}
        
        return {
            "min": round(min(scores), 4),
            "max": round(max(scores), 4),
            "std": round(statistics.stdev(scores) if len(scores) > 1 else 0.0, 4),
            "q25": round(statistics.quantiles(scores, n=4)[0], 4) if len(scores) >= 4 else 0.0,
            "q75": round(statistics.quantiles(scores, n=4)[2], 4) if len(scores) >= 4 else 0.0
        }
        
    except Exception:
        return {}


def calculate_classification_metrics(
    true_labels: List[str],
    predicted_labels: List[str],
    confidence_scores: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Calculate classification performance metrics.
    
    Args:
        true_labels: Ground truth labels
        predicted_labels: Predicted labels
        confidence_scores: Confidence scores for predictions
        
    Returns:
        Dict[str, Any]: Classification metrics
    """
    try:
        if len(true_labels) != len(predicted_labels):
            raise ValueError("True and predicted labels must have same length")
        
        if not true_labels:
            return {"error": "No labels provided"}
        
        # Calculate basic metrics
        correct = sum(1 for true, pred in zip(true_labels, predicted_labels) if true == pred)
        total = len(true_labels)
        accuracy = correct / total
        
        # Calculate per-class metrics
        unique_labels = list(set(true_labels + predicted_labels))
        per_class_metrics = {}
        
        for label in unique_labels:
            tp = sum(1 for true, pred in zip(true_labels, predicted_labels) 
                    if true == label and pred == label)
            fp = sum(1 for true, pred in zip(true_labels, predicted_labels) 
                    if true != label and pred == label)
            fn = sum(1 for true, pred in zip(true_labels, predicted_labels) 
                    if true == label and pred != label)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            
            per_class_metrics[label] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "support": true_labels.count(label)
            }
        
        # Overall metrics
        metrics = {
            "accuracy": round(accuracy, 4),
            "total_samples": total,
            "correct_predictions": correct,
            "per_class_metrics": per_class_metrics
        }
        
        # Add confidence-based metrics if available
        if confidence_scores and len(confidence_scores) == len(predicted_labels):
            avg_confidence = statistics.mean(confidence_scores)
            confidence_correct = [conf for i, conf in enumerate(confidence_scores) 
                                if true_labels[i] == predicted_labels[i]]
            confidence_incorrect = [conf for i, conf in enumerate(confidence_scores) 
                                  if true_labels[i] != predicted_labels[i]]
            
            metrics.update({
                "average_confidence": round(avg_confidence, 4),
                "confidence_correct_avg": round(statistics.mean(confidence_correct), 4) if confidence_correct else 0.0,
                "confidence_incorrect_avg": round(statistics.mean(confidence_incorrect), 4) if confidence_incorrect else 0.0
            })
        
        return metrics
        
    except Exception as e:
        logger.error(f"Classification metrics calculation failed: {str(e)}")
        return {"error": str(e)}


def calibrate_confidence(
    confidence_scores: List[float],
    true_labels: List[bool],
    num_bins: int = 10
) -> Dict[str, Any]:
    """
    Analyze confidence calibration.
    
    Args:
        confidence_scores: Predicted confidence scores
        true_labels: True binary labels (correct/incorrect)
        num_bins: Number of bins for calibration analysis
        
    Returns:
        Dict[str, Any]: Calibration analysis results
    """
    try:
        if len(confidence_scores) != len(true_labels):
            raise ValueError("Confidence scores and labels must have same length")
        
        if not confidence_scores:
            return {"error": "No data provided"}
        
        # Create bins
        bin_edges = [i / num_bins for i in range(num_bins + 1)]
        bin_stats = []
        
        for i in range(num_bins):
            bin_min, bin_max = bin_edges[i], bin_edges[i + 1]
            
            # Find predictions in this bin
            in_bin = [(conf, label) for conf, label in zip(confidence_scores, true_labels)
                     if bin_min <= conf < bin_max or (i == num_bins - 1 and conf == bin_max)]
            
            if in_bin:
                avg_confidence = statistics.mean([conf for conf, _ in in_bin])
                accuracy = statistics.mean([label for _, label in in_bin])
                count = len(in_bin)
                
                bin_stats.append({
                    "bin_range": f"{bin_min:.2f}-{bin_max:.2f}",
                    "count": count,
                    "avg_confidence": round(avg_confidence, 4),
                    "accuracy": round(accuracy, 4),
                    "calibration_error": round(abs(avg_confidence - accuracy), 4)
                })
        
        # Calculate expected calibration error
        total_samples = len(confidence_scores)
        ece = sum(stat["count"] / total_samples * stat["calibration_error"] 
                 for stat in bin_stats)
        
        return {
            "expected_calibration_error": round(ece, 4),
            "bin_statistics": bin_stats,
            "overall_accuracy": round(statistics.mean(true_labels), 4),
            "overall_confidence": round(statistics.mean(confidence_scores), 4)
        }
        
    except Exception as e:
        logger.error(f"Confidence calibration analysis failed: {str(e)}")
        return {"error": str(e)}