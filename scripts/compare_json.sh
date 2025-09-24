#!/bin/bash

git diff --no-index --word-diff=color <(sed 's/\\n//g' compare_results/polars_offer_3.json) <(sed 's/\\n//g' json_file/llm_offer_3.json) > compare_results/offer_3_git_diff.txt
