"""
Topic cluster generation functionality.
"""
import os
import json
from typing import List, Dict, Any, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
from ..types.planning import (
    TopicCluster,
    ContentTopic
)
from ..research.web_researcher import conduct_web_research


class TopicClusterError(Exception):
    """Exception raised for errors in the topic cluster generation process."""
    pass


def generate_topic_clusters(
    niche: str,
    num_clusters: int = 3,
    subtopics_per_cluster: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> List[TopicCluster]:
    """
    Generate topic clusters for a specific niche.
    
    Args:
        niche: The niche to generate topic clusters for.
        num_clusters: The number of clusters to generate.
        subtopics_per_cluster: The number of subtopics per cluster.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated topic clusters.
        
    Raises:
        TopicClusterError: If an error occurs during generation.
    """
    try:
        # Create prompt for topic cluster generation
        prompt = f"""
        Generate {num_clusters} topic clusters for a {niche} blog or website.
        
        Each topic cluster should have:
        1. A main topic (pillar content)
        2. {subtopics_per_cluster} subtopics (cluster content)
        3. 3-5 relevant keywords for the cluster
        
        The main topic should be broad, and the subtopics should be more specific aspects of the main topic.
        
        Return your response in the following format:
        
        Cluster 1:
        Main Topic: [Main Topic]
        Subtopics:
        - [Subtopic 1]
        - [Subtopic 2]
        - [Subtopic 3]
        - [Subtopic 4]
        - [Subtopic 5]
        Keywords: [keyword1, keyword2, keyword3, keyword4, keyword5]
        
        Cluster 2:
        Main Topic: [Main Topic]
        Subtopics:
        - [Subtopic 1]
        - [Subtopic 2]
        - [Subtopic 3]
        - [Subtopic 4]
        - [Subtopic 5]
        Keywords: [keyword1, keyword2, keyword3, keyword4, keyword5]
        
        And so on.
        """
        
        # Generate topic clusters
        clusters_text = generate_text(prompt, provider, options)
        
        # Parse the clusters
        clusters = []
        
        current_main_topic = None
        current_subtopics = []
        current_keywords = []
        
        lines = clusters_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Cluster "):
                # Save previous cluster if it exists
                if current_main_topic and current_subtopics and current_keywords:
                    clusters.append(
                        TopicCluster(
                            main_topic=current_main_topic,
                            subtopics=current_subtopics,
                            keywords=current_keywords
                        )
                    )
                
                # Reset current cluster
                current_main_topic = None
                current_subtopics = []
                current_keywords = []
            elif line.startswith("Main Topic:"):
                current_main_topic = line[11:].strip()
            elif line.startswith("- "):
                current_subtopics.append(line[2:].strip())
            elif line.startswith("Keywords:"):
                keywords_text = line[9:].strip()
                current_keywords = [k.strip() for k in keywords_text.split(",")]
        
        # Add the last cluster if it exists
        if current_main_topic and current_subtopics and current_keywords:
            clusters.append(
                TopicCluster(
                    main_topic=current_main_topic,
                    subtopics=current_subtopics,
                    keywords=current_keywords
                )
            )
        
        return clusters
    except Exception as e:
        raise TopicClusterError(f"Error generating topic clusters: {str(e)}")


def generate_topic_clusters_with_research(
    niche: str,
    num_clusters: int = 3,
    subtopics_per_cluster: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> List[TopicCluster]:
    """
    Generate topic clusters for a specific niche using web research.
    
    Args:
        niche: The niche to generate topic clusters for.
        num_clusters: The number of clusters to generate.
        subtopics_per_cluster: The number of subtopics per cluster.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated topic clusters.
        
    Raises:
        TopicClusterError: If an error occurs during generation.
    """
    try:
        # Conduct web research
        research_results = conduct_web_research([niche, "topics", "keywords"])
        
        # Create prompt for topic cluster generation
        prompt = f"""
        Generate {num_clusters} topic clusters for a {niche} blog or website based on the following research:
        
        {str(research_results)[:2000]}...
        
        Each topic cluster should have:
        1. A main topic (pillar content)
        2. {subtopics_per_cluster} subtopics (cluster content)
        3. 3-5 relevant keywords for the cluster
        
        The main topic should be broad, and the subtopics should be more specific aspects of the main topic.
        
        Return your response in the following format:
        
        Cluster 1:
        Main Topic: [Main Topic]
        Subtopics:
        - [Subtopic 1]
        - [Subtopic 2]
        - [Subtopic 3]
        - [Subtopic 4]
        - [Subtopic 5]
        Keywords: [keyword1, keyword2, keyword3, keyword4, keyword5]
        
        Cluster 2:
        Main Topic: [Main Topic]
        Subtopics:
        - [Subtopic 1]
        - [Subtopic 2]
        - [Subtopic 3]
        - [Subtopic 4]
        - [Subtopic 5]
        Keywords: [keyword1, keyword2, keyword3, keyword4, keyword5]
        
        And so on.
        """
        
        # Generate topic clusters
        clusters_text = generate_text(prompt, provider, options)
        
        # Parse the clusters
        clusters = []
        
        current_main_topic = None
        current_subtopics = []
        current_keywords = []
        
        lines = clusters_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Cluster "):
                # Save previous cluster if it exists
                if current_main_topic and current_subtopics and current_keywords:
                    clusters.append(
                        TopicCluster(
                            main_topic=current_main_topic,
                            subtopics=current_subtopics,
                            keywords=current_keywords
                        )
                    )
                
                # Reset current cluster
                current_main_topic = None
                current_subtopics = []
                current_keywords = []
            elif line.startswith("Main Topic:"):
                current_main_topic = line[11:].strip()
            elif line.startswith("- "):
                current_subtopics.append(line[2:].strip())
            elif line.startswith("Keywords:"):
                keywords_text = line[9:].strip()
                current_keywords = [k.strip() for k in keywords_text.split(",")]
        
        # Add the last cluster if it exists
        if current_main_topic and current_subtopics and current_keywords:
            clusters.append(
                TopicCluster(
                    main_topic=current_main_topic,
                    subtopics=current_subtopics,
                    keywords=current_keywords
                )
            )
        
        return clusters
    except Exception as e:
        raise TopicClusterError(f"Error generating topic clusters with research: {str(e)}")


def generate_content_topics_from_cluster(
    cluster: TopicCluster,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> List[ContentTopic]:
    """
    Generate content topics from a topic cluster.
    
    Args:
        cluster: The topic cluster to generate content topics from.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated content topics.
        
    Raises:
        TopicClusterError: If an error occurs during generation.
    """
    try:
        # Create prompt for content topic generation
        prompt = f"""
        Generate content topics for a blog or website based on the following topic cluster:
        
        Main Topic: {cluster.main_topic}
        Subtopics:
        {", ".join(cluster.subtopics)}
        Keywords: {", ".join(cluster.keywords)}
        
        For each topic (main topic and subtopics), provide:
        1. A compelling title
        2. 3-5 relevant keywords
        3. A brief description (1-2 sentences)
        
        Return your response in the following format:
        
        Topic 1 (Main Topic):
        Title: [Title]
        Keywords: [keyword1, keyword2, keyword3]
        Description: [Description]
        
        Topic 2 (Subtopic 1):
        Title: [Title]
        Keywords: [keyword1, keyword2, keyword3]
        Description: [Description]
        
        And so on.
        """
        
        # Generate content topics
        topics_text = generate_text(prompt, provider, options)
        
        # Parse the topics
        topics = []
        
        current_title = None
        current_keywords = None
        current_description = None
        
        lines = topics_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Topic "):
                # Save previous topic if it exists
                if current_title and current_keywords:
                    topics.append(
                        ContentTopic(
                            title=current_title,
                            keywords=current_keywords,
                            description=current_description
                        )
                    )
                
                # Reset current topic
                current_title = None
                current_keywords = None
                current_description = None
            elif line.startswith("Title:"):
                current_title = line[6:].strip()
            elif line.startswith("Keywords:"):
                keywords_text = line[9:].strip()
                current_keywords = [k.strip() for k in keywords_text.split(",")]
            elif line.startswith("Description:"):
                current_description = line[12:].strip()
        
        # Add the last topic if it exists
        if current_title and current_keywords:
            topics.append(
                ContentTopic(
                    title=current_title,
                    keywords=current_keywords,
                    description=current_description
                )
            )
        
        return topics
    except Exception as e:
        raise TopicClusterError(f"Error generating content topics from cluster: {str(e)}")


def save_topic_clusters_to_json(
    clusters: List[TopicCluster],
    file_path: str
) -> None:
    """
    Save topic clusters to a JSON file.
    
    Args:
        clusters: The topic clusters to save.
        file_path: The path to save the clusters to.
        
    Raises:
        TopicClusterError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Convert clusters to JSON-serializable format
        clusters_data = []
        
        for cluster in clusters:
            cluster_data = {
                "main_topic": cluster.main_topic,
                "subtopics": cluster.subtopics,
                "keywords": cluster.keywords
            }
            
            clusters_data.append(cluster_data)
        
        # Write clusters to JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(clusters_data, f, indent=2)
    except Exception as e:
        raise TopicClusterError(f"Error saving topic clusters to JSON: {str(e)}")


def load_topic_clusters_from_json(
    file_path: str
) -> List[TopicCluster]:
    """
    Load topic clusters from a JSON file.
    
    Args:
        file_path: The path to load the clusters from.
        
    Returns:
        The loaded topic clusters.
        
    Raises:
        TopicClusterError: If an error occurs during loading.
    """
    try:
        # Read clusters from JSON
        with open(file_path, "r", encoding="utf-8") as f:
            clusters_data = json.load(f)
        
        # Convert JSON data to TopicCluster objects
        clusters = []
        
        for cluster_data in clusters_data:
            cluster = TopicCluster(
                main_topic=cluster_data["main_topic"],
                subtopics=cluster_data["subtopics"],
                keywords=cluster_data["keywords"]
            )
            
            clusters.append(cluster)
        
        return clusters
    except Exception as e:
        raise TopicClusterError(f"Error loading topic clusters from JSON: {str(e)}")


def visualize_topic_cluster(
    cluster: TopicCluster,
    output_format: str = "mermaid"
) -> str:
    """
    Visualize a topic cluster.
    
    Args:
        cluster: The topic cluster to visualize.
        output_format: The output format for the visualization.
        
    Returns:
        The visualization.
        
    Raises:
        TopicClusterError: If an error occurs during visualization.
    """
    try:
        if output_format == "mermaid":
            # Create Mermaid diagram
            mermaid = "graph TD\n"
            
            # Add main topic
            main_topic_id = "main"
            mermaid += f"    {main_topic_id}[{cluster.main_topic}]\n"
            
            # Add subtopics
            for i, subtopic in enumerate(cluster.subtopics):
                subtopic_id = f"sub{i+1}"
                mermaid += f"    {subtopic_id}[{subtopic}]\n"
                mermaid += f"    {main_topic_id} --> {subtopic_id}\n"
            
            return mermaid
        else:
            raise TopicClusterError(f"Unsupported output format: {output_format}")
    except Exception as e:
        raise TopicClusterError(f"Error visualizing topic cluster: {str(e)}")
