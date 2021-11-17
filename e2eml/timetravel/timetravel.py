import pandas as pd
import numpy as np
import warnings
import logging
import dill as pickle
import gc
from e2eml.classification.classification_blueprints import ClassificationBluePrint
from e2eml.regression.regression_blueprints import RegressionBluePrint
from e2eml.full_processing import postprocessing


class TimeTravel():

    def call_preprocessing_functions_mapping(self, class_instance):
        class_instance.preprocessing_funcs = {
            "automatic_type_detection_casting": {"func": class_instance.automatic_type_detection_casting, "args": None},
            "remove_duplicate_column_names": {"func": class_instance.remove_duplicate_column_names, "args": None},
            "reset_dataframe_index": {"func": class_instance.reset_dataframe_index, "args": None},
            "fill_infinite_values": {"func": class_instance.fill_infinite_values, "args": None},
            "early_numeric_only_feature_selection": {"func": class_instance.automated_feature_selection, "args": (None, None, True)},
            "delete_high_null_cols": {"func": class_instance.delete_high_null_cols, "args": (0.05)},
            "data_binning": {"func": class_instance.data_binning, "args": None},
            "regex_clean_text_data": {"func": class_instance.regex_clean_text_data, "args": None},
            "handle_target_skewness": {"func": class_instance.target_skewness_handling, "args": ("fit")},
            "datetime_converter": {"func": class_instance.datetime_converter, "args": ("all")},
            "pos_tagging_pca": {"func": class_instance.pos_tagging_pca, "args": (True)},# slow with many categories
            "append_text_sentiment_score": {"func": class_instance.append_text_sentiment_score, "args": None},
            "tfidf_vectorizer_to_pca": {"func": class_instance.tfidf_vectorizer_to_pca, "args": (True)}, # slow with many categories
            "tfidf_vectorizer": {"func": class_instance.tfidf_vectorizer_to_pca, "args": (False)},
            "rare_feature_processing": {"func": class_instance.rare_feature_processor, "args": (0.005, 'miscellaneous', class_instance.rarity_cols)},
            "cardinality_remover": {"func": class_instance.cardinality_remover, "args": (100)},
            "holistic_null_filling": {"func": class_instance.holistic_null_filling, "args": (False)}, # slow
            "numeric_binarizer_pca": {"func": class_instance.numeric_binarizer_pca, "args": None},
            "onehot_pca": {"func": class_instance.onehot_pca, "args": None},
            "category_encoding": {"func": class_instance.category_encoding, "args": ("target")},
            "fill_nulls_static": {"func": class_instance.fill_nulls, "args": ("static")},
            "outlier_care": {"func": class_instance.outlier_care, "args": ('isolation', 'append')},
            "remove_collinearity": {"func": class_instance.remove_collinearity, "args": (0.8)},
            "skewness_removal": {"func": class_instance.skewness_removal, "args": (False)},
            "clustering_as_a_feature_dbscan": {"func": class_instance.dbscan_clustering, "args": None},
            "clustering_as_a_feature_kmeans_loop": {"func": class_instance.kmeans_clustering_loop, "args": None},
            "clustering_as_a_feature_gaussian_mixture_loop": {"func": class_instance.gaussian_mixture_clustering_loop, "args": None},
            "pca_clustering_results": {"func": class_instance.pca_clustering_results, "args": None},
            "autotuned_clustering": {"func": class_instance.auto_tuned_clustering, "args": None},
            "reduce_memory_footprint": {"func": class_instance.reduce_memory_footprint, "args": None},
            "scale_data": {"func": class_instance.data_scaling, "args": None},
            "smote": {"func": class_instance.smote_binary_multiclass, "args": None},
            "automated_feature_selection": {"func": class_instance.automated_feature_selection, "args": (None, None, False)},
            "bruteforce_random_feature_selection": {"func": class_instance.bruteforce_random_feature_selection, "args": None}, # slow
            "delete_unpredictable_training_rows": {"func": class_instance.delete_unpredictable_training_rows, "args": None},
            "autoencoder_based_oversampling": {"func": class_instance.autoencoder_based_oversampling, "args": None},
            "synthetic_data_augmentation": {"func": class_instance.synthetic_data_augmentation, "args": None},
            "final_pca_dimensionality_reduction": {"func": class_instance.final_pca_dimensionality_reduction, "args": None},
            "sort_columns_alphabetically": {"func": class_instance.sort_columns_alphabetically, "args": None},
        }

    def create_time_travel_checkpoints(self, class_instance, checkpoint_file_path=None, df=None):
        """
        Our recommended blueprint for Tabnet testing.
        Runs a preprocessing blueprint only. This is useful for building custom pipelines.
        :param class_instance: Accepts a an e2eml Classification or Regression class instance. This does not support
        NLP transformers.
        :param checkpoint_file_path: (Optional). Takes a file path to store the saved class instance checkpoints.
        On default will save in current location.
        :param df: Accepts a dataframe to make predictions on new data.
        :return: Saves the checkpoints locally.
        """
        logging.info('Start blueprint.')
        class_instance.runtime_warnings(warn_about="future_architecture_change")
        class_instance.check_prediction_mode(df)
        class_instance.train_test_split(how=class_instance.train_split_type)
        self.last_checkpoint_reached = "train_test_split"

        self.call_preprocessing_functions_mapping(class_instance=class_instance)

        for key, value in class_instance.blueprint_step_selection_non_nlp.items():
            if class_instance.blueprint_step_selection_non_nlp[key] and not class_instance.checkpoint_reached[key]:
                if (key == "regex_clean_text_data" and len(class_instance.nlp_transformer_columns) > 0) or \
                        (key == "tfidf_vectorizer" and len(class_instance.nlp_transformer_columns) > 0) or \
                        (key == "append_text_sentiment_score" and len(class_instance.nlp_transformer_columns) > 0) or \
                        (key not in ["regex_clean_text_data", "tfidf_vectorizer", "append_text_sentiment_score",
                                     "train_test_split"]):
                    if class_instance.preprocessing_funcs[key]["args"]:
                        try:
                            if len(np.array(class_instance.preprocessing_funcs[key]["args"])) == 1:
                                class_instance.preprocessing_funcs[key]["func"](class_instance.preprocessing_funcs[key]["args"])
                            else:
                                class_instance.preprocessing_funcs[key]["func"](*class_instance.preprocessing_funcs[key]["args"])
                        except TypeError:
                            class_instance.preprocessing_funcs[key]["func"](class_instance.preprocessing_funcs[key]["args"])
                    else:
                        class_instance.preprocessing_funcs[key]["func"]()
                else:
                    print(f"Skipped preprocessing step {key} as it has not been selected by user.")
                class_instance.checkpoint_reached[key] = True
                self.last_checkpoint_reached = key
                postprocessing.save_to_production(class_instance, file_name=f'blueprint_checkpoint_{key}', clean=False,
                                                  file_path=checkpoint_file_path)
            else:
                pass

    def load_checkpoint(self, checkpoint_to_load=None, checkpoint_file_path=None):
        """
        This function loads saved checkpoints on demand. If no checkpoint is specified, it loads the most recent
        checkpoint executed in the pipeline.
        :param checkpoint_to_load: Takes a string, specifying the checkpoint to load. All strings can be looked up
        in blueprint_step_selection_non_nlp class attribute. Only checkpoints, which have been saved explicitely can be
        loaded. If no checkpoint is specified, it loads the most recent
        checkpoint executed in the pipeline.
        :param checkpoint_file_path: (Optional) Takes a string. On default loads checkpoint from current path. If specified,
        loads the checkpoint from this path.
        :return: Returns loaded checkpoint.
        """
        if not checkpoint_to_load:
            class_instance = postprocessing.load_for_production(file_name=f'blueprint_checkpoint_{self.last_checkpoint_reached}',
                                                                file_path=checkpoint_file_path)
        else:
            class_instance = postprocessing.load_for_production(file_name=f'blueprint_checkpoint_{checkpoint_to_load}',
                                                                file_path=checkpoint_file_path)
        return class_instance

