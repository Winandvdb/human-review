# 2026-10-07 — live polish during the Devoxx talk

Victor polished two human-review demo reports live on 7 Oct, before and during his Devoxx Belgium talk (16:40). The reports were petclinic **PR #51** (branch `Devoxx26`, "Owners grid", served on :7654) and petclinic-pr-visit-has-vet **PR #49** (branch `test-pr`, "Link Visit with Vet", served on :7655). Each ask was first hand-patched into both `review.html` files: `live-patch-*` `<style>`/`<script>` blocks, plus a few plain text replacements. Subagents then ported the ask into the build scripts in `victorrentea/human-review` and proved it on the `petclinic-pr-owner-grid-paginated` workbench. A few changes also went to `code-city` and `OpenAPI-Visual-Diff`.

Notes on the tables:
- **Time asked** is local time (CEST, UTC+2), the same clock as the commit times.
- **Patch** ids are from the PR #51 page. The PR #49 page carries a subset with the same ids.
- **Verified by:** a test marked *(edited)* is an existing test the commit changed. Unmarked tests were added by the commit.
- **Repo prefixes:** `cc:` is a commit in `code-city`, `ovd:` is a commit in `OpenAPI-Visual-Diff`.

## Masthead / header & tab strip

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| Chip row ~30% shorter, top space halved | 12:49 | — | ff2739a | — |
| Drop the word "grade" from the score badge | 12:49 | — | ff2739a | — |
| Less space above the title, 🔗 "connected" on VSC, less air after "/10" | 13:28 | 1328, 1350 | c79e999, 121d3c7 (🔗 rule swept in) | — |
| Tab labels: "Code City"→"City", "Logging"→"Logs", "CODEOWNERS"→"Codeowners" | 13:33–13:34 | — (text) | c79e999 | — |
| Behind-main marker as "5↓main" (plain ↓, bold amber) | 13:34–13:36 | 1334 | c79e999 | `test_build_review.py::test_the_mark_ends_the_ref_chip_and_carries_its_own_tooltip` *(edited, in 48542b3)* |
| Title-row badges (VSC, Served, rings, grade) as tall as the text | 14:23 | 1422, 1424, 1425, 1432 | db59645 | — |
| Half the gap between tab label and rerun wheel; badges at the letters' height; centre "5/10" | 14:36 | masthead-r4 | 6044460 | — |
| Emojis centred inside the round rerun rings | 15:15 | 1516 | d9eb1ae | — |
| Rerun icons leave the tab strip for each tab's own title; one header font | 15:10 | tabicons, tabicons-2…-6, tabicons-js, tabicons-4-js, tabicons-6-js | 51ed474 | `test_action_server.py::test_a_titled_tab_gets_its_presses_at_the_end_of_its_title`, `::test_the_review_tab_gets_them_at_the_end_of_its_pile_line_not_on_a_later_h2`, `::test_the_api_tab_gets_them_after_the_last_word_of_its_verdict_band`, `::test_an_untitled_tab_with_presses_is_given_its_label_and_one_without_is_left_alone`, `::test_the_strip_styles_and_the_progress_bar_no_longer_look_for_presses_on_the_strip` |
| A quiet tab (no changes) is faded, not struck through | 15:44 | 1544 | 36a0f70 | `test_ux_polish.py::test_3_a_quiet_tab_is_faded_not_struck_through` (added in d4fc02b) |
| Commits added after the review: a "N↑" marker before the branch name, hover lists them (the Review band goes, see Review) | 15:48 | 1549 | d0a08f1 | `test_ahead_marker.py::test_commits_after_the_review_are_listed_newest_first`, `::test_nothing_after_the_review_means_no_marker`, `::test_the_marker_sits_right_before_the_head_ref_with_a_listing_tip` |
| "+N outside commits" badge looks like 5↓main (no pill/caret); tooltip as a bullet list | 16:18 | 1620, 1621 | d4fc02b, 0e1c5d6, d0a08f1 (`tiplist.prose`) | `test_ux_polish.py::test_11_the_branch_badge_does_not_make_the_masthead_taller` |
| "+1" badge placed before the head branch, like 7↑ | 20:05 | plus1 | da604d1 | — |
| Rerun icon vertically aligned with every heading ("third time") | 20:02, 20:27 | iconalign | da604d1, 397f613 | `test_title_icons_centred.py::test_the_rings_sit_on_the_middle_of_the_titles_capitals` |
| Use more width at 150% zoom (side margin like at 175%) | 20:12 | widen | da604d1 | — |
| Branch chip not orange-bordered when drifted | 20:12 | widen | da604d1 | `test_ux_polish.py::test_11_the_branch_badge_does_not_make_the_masthead_taller` *(edited)* |
| VSC chip shows a 🔌 plug, not 🔗 | 20:13 | vscplug | da604d1 | — |
| Tabs as tall as the badges above them (19.75px) | 20:33 | tabh | da604d1 | — |

## Review

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| Review chip: angry-bot image before "9 open", "·" becomes "/" | 15:12 | 1515 | 8baeba8, 757a170 | `test_build_review.py::test_the_review_chip_face_is_counts_only_so_the_scope_bar_keeps_one_row` *(edited)*, `::test_the_review_chip_leads_with_what_is_left_to_do` *(edited)* |
| Publish on GitHub: one plain confirmation (body expandable), no call list; fix the refused/partial posting | 15:29 | prpush-css, prpush | 80d90e5 | `test_pr_push_dialog.py::test_post_asks_one_question_and_shows_comments_not_calls`, `::test_cancel_posts_nothing_and_gives_the_button_back`, `::test_a_partial_record_renders_retry_and_its_sentence`; `test_push_pr_comments.py::test_a_504_on_a_review_that_was_created_anyway_posts_nothing_twice`, `::test_many_comments_go_out_in_reviews_of_batch_the_first_carrying_the_summary` |
| Grade panel: "capped" (hover explains) instead of struck "was N"; ✅ after "CI green" | 15:32 | 1531 | 23af6d7 | `test_build_review.py::test_the_grade_reasons_are_computed_from_what_the_page_measured` *(edited)*, `::test_ci_green_links_to_the_run_it_rests_on` *(edited)* |
| Diffs collapsed by default under their file bar; drop the opaque "vs <sha>" | 15:32 | ghfold-css, ghfold, 1533 | 1d8ed40 | `test_build_review.py::test_a_fixed_card_shows_the_fix_commits_hunks_whenever_one_follows_the_implementation` *(edited)* |
| Drop the "N commits since the agent finished" band and the "landed after the review" grade bullet | 15:48 | 1549 | d0a08f1 | `test_ahead_marker.py::*` (see Masthead) |
| Published comments show their "on GitHub ↗" links | 15:56 | — (injected links) | 80d90e5 | `test_pr_push_dialog.py::test_everything_posted_reads_published_and_opens_the_review` |
| No tooltip (value interval) on the assumption confidence chip | 15:56 | — | 7f6d474 | `test_build_review.py::test_an_assumptions_confidence_reads_verbatim_with_its_tooltip` *(edited)* |
| Every excerpt longer than one line folds; stat on the right | 16:00 | snipfold, 1600 | 1d8ed40 | `test_build_review.py::test_a_long_quote_opens_on_its_anchored_lines_and_folds_the_rest` *(edited)* |
| "in VS Code" link with VS Code icon beside each "on GitHub" (GitHub PR extension) | 16:00, 16:05, 16:19 | prpush | 80d90e5 | `test_pr_push_dialog.py::test_the_build_puts_in_vs_code_beside_every_github_link`, `::test_in_vs_code_brings_the_checkouts_window_forward_then_opens_the_pr`, `::test_editor_js_sends_the_item_link_with_its_thread` |
| File name always on the left; confidence chip at title size, red/amber/green | 20:34 | review-sym, review-sym-js | a54c4b7 | `test_build_review.py::test_a_confidence_chip_is_coloured_red_amber_green_by_band`, `::test_the_confidence_chip_is_as_big_as_the_title_and_on_its_baseline`, `::test_an_inline_snippet_names_its_file_on_the_left_like_a_folded_one` |

## Demo

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| Drop the "Not filmed. Touched by this change" transcript row | 12:35 | — (text) | c40887e | `test_build_review.py::test_a_page_link_the_film_never_showed_is_not_printed` |
| Start App in Docker shows each container coming up (grey/green/red chips) | 13:45 | docker-status, docker-status-js | 3f47832 | `test_compose_status.py::test_each_container_state_has_one_light`, `::test_the_images_then_the_containers_are_chips_while_start_runs`, `::test_a_failed_start_keeps_the_red_chip_with_the_reason_on_hover` (+12 more in that file) |
| Band reads "Running app", not "Deployed" | 13:53 | — (text) | 3f47832 | — |
| Show progress and the URL without a page refresh | 14:27 | docker-status-js | 73f7b38 | `test_compose_status.py::test_a_page_reloaded_mid_start_picks_the_run_up_by_itself`, `::test_with_no_start_in_flight_the_page_does_not_press_it` |
| Transcript ends at the video's height; less space under the video | 15:00 | 1505 | 51ed474 | `test_build_review.py::test_the_film_title_heads_the_transcript_column_not_a_row_above_the_player` |
| Container chips on their own line; space between the tab strip and the band | 15:17 | 1517 | cb9ee86 | — |
| "Intro video", not "Demo video"; title moved over the transcript column | 15:23, 15:49 | tabicons-6, tabicons-6-js | 51ed474 | `test_build_review.py::test_the_film_title_heads_the_transcript_column_not_a_row_above_the_player` |
| Voices: 👩 standard, 🐘 (no "guess who"), 🌍 Discovery; moved into the "Intro video" title row | 16:22 | voicemove, 1622, 1624, 1626, tabicons-7 | cd61985 | `test_build_review.py::test_with_a_deployed_app_row_the_voices_still_sit_in_the_film_title_row`, `test_ux_polish.py::test_17c_voices_are_emoji_faces_each_with_a_spoken_name` |
| Coloured dot per DB fixture (also on Tests E2E rows); tip "DB Fixture: default"; a click opens the data | 20:22, 20:32, 20:33 | fixture-dots-css, fixture-dots | a4749e3 | `test_fixtures.py::test_unconfigured_fixtures_take_the_palette_in_folder_order`, `::test_configured_colour_wins_and_the_palette_skips_it`, `::test_each_test_starts_from_what_its_code_says`, `::test_the_script_words_the_tip_like_the_demo_bar_and_opens_the_dataset` |
| 👁 dataset quick view per fixture button (tables by outgoing FKs, side by side) | 20:27 | dataset-view, dataset-view-js | e483e8d (swept in under the caret commit) | `test_dataset_view.py::test_tables_are_ordered_by_outgoing_foreign_keys_first`, `::test_the_eye_opens_and_closes_that_fixtures_tables_and_does_not_reset`, `::test_every_reset_button_gets_an_eye_even_the_ones_the_probe_adds_later` (+7 more) |
| A rounded pill around each voice radio, aligned with the title | 20:27 | iconalign | 397f613 | `test_title_icons_centred.py::test_each_voice_is_one_pill_on_the_title_row_centred_on_its_capitals` |

## Tests

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| "UI" level renamed "E2E" (Unit/API unchanged) | 12:59 | — | 18a02a8 | `test_reqmap_layout.py::test_a_models_ui_label_is_renamed_e2e_at_build_time` |
| Card title tooltip: how the list was computed | 13:05 | — | b472053 | `test_reqmap_layout.py::test_the_card_title_says_how_the_list_was_computed` |
| Space between the ledger numbers; "Issue #N" in link blue | 13:05 | tledger, 1312 | b472053 | — |
| Traced E2E tests were hidden in the folded group: give them their own open group | 13:22 | — | 8693c82 | `test_reqmap_layout.py::test_a_traced_test_is_never_folded_out_of_the_covering_card` |
| Semantic pairing missed tests: re-pair, and warn when the pairing is older than the coverage | 13:25 (approved 14:28) | — | bd86c6b | `test_pairing_stale.py::test_a_mapping_older_than_the_coverage_is_stale`, `::test_the_build_warns_and_the_page_says_so`, `::test_nothing_on_the_stale_path_calls_a_model` (+8 more) |
| Coverage shield (IntelliJ) instead of the ruler and on every row; shorter tooltip; half the gap between icons; Playwright icon | 13:25–13:27 | 1326 | 1a09a40, 84e454b (🎭 moves to the recording) | `test_reqmap_layout.py::test_the_card_title_says_how_the_list_was_computed` *(edited)*, `test_build_review.py::test_the_recordings_are_a_registry_the_tv_reads_not_a_list` *(edited)* |
| Row heads vertically centred, bigger chevron, equal gaps at the row end, checkbox inside the filter pill, "on <date>" without "opened" | 13:38–13:39 | 1338, 1339, 1348 | 26536db | — |
| E2E pill in solid orange (Tests and Sequence) | 13:52 | 1351 | 01daeff | — |
| No window scrollbar: the tab is one window tall | 14:23 | tests-tab, tests-tab-js | f4b71a6 | `test_reqmap_layout.py::test_the_tab_is_exactly_one_window_tall_footer_included`, `::test_the_fit_script_rides_with_the_matrix_and_the_sheet_reads_it` |
| Show only the file extension, in blue; the shield shares the title's tooltip (relayed from the walkie session) | 14:20 | tests-tab | f4b71a6 | `test_semcov.py::test_a_rows_file_is_named_by_its_kind_alone` |
| Level pills one width, centred; filter badges get more room | 14:40 | 1440 | 0e0343e | `test_reqmap_layout.py::test_the_row_pills_are_one_width_and_the_filters_have_room` |
| Filter badges show the hand cursor (clickable), not "?" | 15:21 | 1522 | 9938bdd | `test_reqmap_layout.py::test_the_row_pills_are_one_width_and_the_filters_have_room` *(edited)* |
| Gap between the two cards equals the 20px page gutter, at any zoom | 15:52 | 1552 | 94489b5 | `test_reqmap_layout.py::test_the_tab_is_exactly_one_window_tall_footer_included` *(edited)* |
| Underline only the extension; preview shows the test body only; ⇥ for the sequence link, 🎭 for the replay | 20:17–20:18 | tests-all | d0a58cf | `test_reqmap_layout.py::test_the_extension_is_underlined_alone_and_the_preview_is_the_body_alone` |
| Group by kind of test (E2E/API/UNIT chapters, collapsible) instead of by ticket sentence; labels kept, no checkboxes | 20:19, 20:24 | tests-chapters, tests-chapters-js | d0a58cf | `test_reqmap_layout.py::test_the_card_is_read_in_chapters_by_kind_not_by_sentence`, `::test_the_title_row_keeps_its_paragraph_and_drops_the_chips` |
| "All tests" checkbox, placed inside the card header | 20:17, 20:32 | tests-chapters, tests-chapters-js | d0a58cf | `test_reqmap_layout.py::test_the_title_row_over_the_card_offers_all_tests_where_the_filters_stood`, `::test_the_inventory_is_every_test_that_ran_minus_the_card`, `::test_a_row_of_the_rest_of_the_run_keeps_every_column_and_opens_nothing` |
| Title tooltip: "as captured by a coverage probe", no count | 20:37 | tests-chapters-js | d0a58cf | — |
| Shield popover listing the covered files (hoverable, linked); chapters with caret, tint and their own counts, collapsed at start; strip 15–20% shorter | 20:39 | tests-chapters, tests-chapters-js | 862c7e2 | `test_reqmap_layout.py::test_the_shield_opens_a_popover_of_the_code_the_test_runs`, `::test_the_cover_list_puts_changed_files_first_and_caps_the_rest`, `::test_a_chapter_heading_is_caret_badge_subtitle_then_its_own_counts` |

## Sequence

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| SQL panel draggable by its head | 12:55 | drag-css, drag | ce33b26 | `test_diagram_views.py::test_genseq_panel_head_is_a_drag_handle` |
| One badge per test: grey circled @ (tagged), + (new), ✍️ (edited), in separate circles | 12:57, 12:59, 13:02 | seqwhy | 4d8f5f4 | `test_build_review.py::test_a_picture_says_whether_it_is_there_by_tag_or_because_the_branch_wrote_the_test` *(edited)* |
| Level pill E2E/API only; language shown as the file extension at the row's right end | 12:59, 13:02, 13:11, 14:17 | seqlang, 1312, seqlang-final | 4d8f5f4, 3cdbf7c | `test_build_review.py::test_a_pair_says_what_kind_of_test_drew_it` *(edited)* |
| Drop the "Also traced: … over the cap of 6" line | 12:48, 13:37 | — (text) | 48542b3 | `test_build_review.py::test_a_picture_says_whether_it_is_there_by_tag_or_because_the_branch_wrote_the_test` *(edited)* |
| Badge tooltip "Decided to trace it because it is new" | 13:37 | — (text) | f3f2684 | `test_build_review.py::test_a_picture_says_whether_it_is_there_by_tag_or_because_the_branch_wrote_the_test` *(edited)* |
| Fold caret twice as big | 14:17, 14:40 | seqlang-final, 1440 | 3cdbf7c, 10a751a | — |
| Half the space left and right of the arrows | 14:38 | 1437 | 10a751a | — |
| Row links the test file (full name, no line numbers) with its new/edited icon; drop the "Show Test" fold | 14:25 | seqfile, seqfile-js | 10a751a | `test_build_review.py::test_the_row_links_the_test_file_instead_of_quoting_the_test`, `test_diagram_views.py::test_the_pair_links_its_test_instead_of_quoting_it`, `::test_a_diagram_nobody_quoted_still_names_and_links_its_test` |
| File icon readable (green/amber/grey); the same CSS everywhere | 14:51 | 1452 | 10a751a | — |
| Arrows 20% smaller and grey, blue on row hover; one underline, not two | 15:06 | 1506 | 10a751a | — |
| Two traced visit-vet tests drew nothing (pictures dropped after a later commit) | 14:28 (approved) | — | b469e92 | `test_genseq_overlay.py::test_a_commit_that_touched_no_diagram_keeps_every_traced_picture`, `::test_a_diagram_a_later_commit_changed_is_read_from_the_work_tree` (+3 more) |

## Structure / diagrams (draw.io, PlantUML, C4) — Data and Structure tabs

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| draw.io card: drop "This diagram is…"; link "Java Domain Model" to VS Code; four buttons (Edit on desktop, Edit on web, Update report, Revert changes) | 13:14 | — (markup) | 121d3c7 | `test_diagram_views.py::test_both_editors_are_offered_and_named` *(edited)*, `::test_the_edit_offer_sits_where_the_caption_sentence_used_to` *(edited)* |
| Thicker lines and borders; the same buttons on the Deployment card; ✏️ / ↺ / ⇤ icons | 13:18–13:21 | 1318 | 121d3c7 | `test_diagram_views.py::test_the_inline_drawio_lines_are_thickened_but_only_default_ones`, `::test_a_traced_diagram_with_undrawn_calls_is_not_the_unchanged_card` |
| Edit buttons with an orange border | 13:21 | 1321 | 121d3c7 | — |
| Buttons never underline; a slight lift on hover | 15:07 | 1507 | a10593f | — |
| One rerun set per card; "DB" card titled "Database"; "Update report" renamed "Load changes"; Structure gets a "Structure diagrams" title | 15:10 | tabicons-3, tabicons-js | 51ed474 | `test_action_server.py::test_the_data_tab_gets_one_set_per_card_after_each_title`, `::test_the_db_diagram_is_titled_database`, `::test_structure_is_given_a_title_and_its_presses_end_it` |
| DB badge "schema only" becomes "unchanged" | 20:02 | — (text) | da604d1 | `test_diagram_views.py::test_a_picture_unchanged_over_a_schema_that_changed_wears_its_own_badge` *(edited)* |
| Conceptual Model: drop "Load changes" (the ring does it); ↺ on Revert; no ▶; buttons in the card header | 20:07 | cm-actions | 16fe638 | `test_diagram_views.py::test_the_action_buttons_sit_in_the_card_header`, `::test_a_button_in_the_header_does_not_flip_the_picture` |
| PlantUML neighbour-radius switch morphs instead of jumping | 20:41 | dgm-morph | 09809b0 | `test_dgm_morph.py::test_the_change_stays_put_the_shared_boxes_slide_and_nothing_is_left_behind`, `::test_reduced_motion_keeps_the_anchor_and_the_glow_but_does_not_slide`, `::test_the_chooser_pins_so_the_anchoring_scroll_never_takes_it_away` |
| C4 views rendered by Structurizr in the Structure tab | 20:53 | — (spliced in, no live-patch id) | e104115, d0ae9e8 | `test_structurizr_views.py::test_a_changed_view_toggles_new_and_old_with_no_diff_pane`, `::test_the_note_says_which_level_a_test_checks`, `::test_a_repository_without_a_workspace_draws_nothing_and_says_nothing` (+8 more) |
| draw.io Diff/New/Old swap animated like PlantUML | 21:37 | drawio-morph, drawio-morph-js | 4cd1dcb | `test_dgm_morph.py::test_a_drawio_swap_slides_shared_boxes_matches_a_renamed_one_by_label_and_settles_clean`, `::test_a_drawio_swap_with_nothing_moved_leaves_the_picture_alone`, `::test_reduced_motion_on_a_drawio_swap_glows_but_does_not_slide` |

## Complexity

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| Lede: drop ", scored as SonarSource defines it" | 12:44 | — (text) | 8bd56f8 | `test_endpoint_complexity.py::test_a_node_folds_open_onto_its_own_lines_and_only_the_arrow_navigates` *(edited)* |
| Name the two numbers "added" and "total" on each group header | 13:34 | 1334 | e10124a | `test_endpoint_complexity.py::test_the_group_header_names_the_two_numbers_over_their_own_columns` |
| A real parser for the call graph (CodeGraphContext tried and rejected by the eval) → JavaParser engine, default after an adversarial eval | 12:47, 15:20, 15:27 | — | 0e68810, 408c1ee | `test_complexity_engines.py::test_the_javaparser_engine_matches_the_hand_computed_flow`, `::test_the_lede_names_the_engine_that_produced_the_numbers`, `::test_without_a_jdk_the_regex_engine_answers_and_says_so` (+7 more); `test_endpoint_complexity.py::test_a_method_named_record_is_filed_and_called_and_a_record_type_is_not_a_method` |
| "Added" header in green, "total" in bright white/bold | 20:35 | cxcols, cxcols-js | da604d1 | `test_endpoint_complexity.py::test_the_group_header_names_the_two_numbers_over_their_own_columns` *(edited)* |

## API

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| Verdict band counts the endpoints broken, not the changes; "double-checked by" becomes "and" | 12:36 | — (text) | 3806a78 | `test_openapi_compat.py::test_the_breaking_panel_counts_the_endpoints_broken_and_nothing_else`, `::test_the_band_counts_the_endpoints_oasdiff_broke_end_to_end` (+2 more) |
| "our openapi-diff.py" | 13:12 | — (text) | a9a21ec | `test_openapi_compat.py::test_the_breaking_panel_counts_the_endpoints_broken_and_nothing_else` *(edited)* |
| Drop our openapi-diff.py: oasdiff is the only differ (after an eval) | 13:44 | — (text) | ab6ca40 | `test_openapi_compat.py::test_the_band_names_one_differ_and_it_is_not_ours` |
| Visual diff: no spine down a controller's list; a collapsed controller reads grey | 15:24 | apishadow | ddc33a1, ovd:156e8e8 | — |
| Toolbar follows the colour scheme; INFO readable on dark (adversarial review) | 15:22 | uxpolish-js | 36a0f70, ovd:79368c0 | `test_ux_polish.py::test_12_the_api_toolbar_follows_the_scheme_and_info_reads_on_dark` (added in d4fc02b) |
| Reads as a diff: no spec title or description (version small in the corner), controller band, compact parameters, Schema first, responses fold by status (2xx open) | 20:05 | api-polish | 7ca68e3, ovd:493ad7e | `test_openapi_visual_diff.py::test_an_operation_reads_as_a_diff_not_as_a_console` |

## UX

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| Title "UX design system"; drop "— control from outside the design system"; plainer gap wording | 13:04 | — (text) | 2ee484d | `test_ds_audit.py::test_the_badge_names_the_verdict_and_not_an_arrow_between_two_words` *(edited)*, `::test_a_lone_material_select_is_the_gap_where_combo_belongs` *(edited)* |
| Shared ▶/▼ caret (Complexity look); tooltip on "N of N screens changed" | ~13:15 (relayed) | 1312 | 23f9861 | `test_ds_audit.py::test_the_count_has_a_tooltip_that_names_each_side_once` |
| Shorter tooltip, plus a collapsible, structured "how changed is decided" box | 13:40 | 1340, dsahow | eafd0a8 | `test_ds_audit.py::test_the_count_opens_a_box_that_names_each_side_once` |
| The title had drifted back on PR #49 (stale fragment); the UX tab turns amber when the branch adds a gap | 20:13 | — (fragment regenerated) | 3c838f3 | `test_ux_tab.py::test_a_fragment_drawn_by_older_code_is_redrawn_from_its_json`, `::test_a_gap_the_branch_added_turns_the_ux_pill_amber`, `::test_a_gap_the_base_already_had_leaves_the_pill_alone` (+5 more) |

## Logging

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| Tab label "Logs"; rerun icons at the end of its title | 13:33, 15:10 | tabicons | c79e999, 51ed474 | `test_action_server.py::test_a_titled_tab_gets_its_presses_at_the_end_of_its_title` |

## Codeowners

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| Title "Needs approval as per .github/CODEOWNERS" | 14:36 | — (text) | 00a11a2 | `test_codeowners.py::test_the_tab_opens_on_the_codeowners_file_it_was_read_from` *(edited)* |
| A monospace link's underline clears its underscores (adversarial review) | 15:22 | uxpolish | 36a0f70 | `test_ux_polish.py::test_15_a_monospace_link_underline_clears_its_underscores` (added in d4fc02b) |

## City

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| Default colour is a metric the PR changed: Δ outgoing coupling (Δ fan-out / fan-in, diverging) | 20:48 | — (shot replaced) | 2a3580f, cc:bc6279e, cc:42c7596, cc:920710a | `test_city_step.py::test_capture_names_the_colour_the_shot_was_taken_in`, `::test_the_colour_rides_into_the_lit_note` |
| First-run intro cards fit their text (adversarial review) | 15:22 | — | cc:6a6d00a | — |

## Cost

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| A time column per phase (implementation, review, fixes, report), plus a total | 10:26 | — | 8175f73 | `test_harness_cost.py::test_a_phase_takes_its_turns_not_the_pauses_between_them`, `::test_the_four_rows_carry_a_time_column_and_a_dash_when_untimed`; `test_adopt.py::test_a_header_cell_marked_data_adopt_takes_the_button_instead_of_the_last` |
| "Token costs" title with the prompt pill on its row; muted session ids; no "fork → prepare" or dates; sessions as sub-rows | 20:09 | cost-v1 | 6cb61ff | `test_harness_cost.py::test_several_sessions_are_a_breakdown_under_the_row_not_a_line_of_prices` |
| "Something is fishy": don't bill the session the branch reverted | 20:09 | cost-v1 | 6cb61ff | `test_harness_cost.py::test_a_branch_reset_to_its_base_forgets_who_wrote_what_it_undid`, `::test_a_recorded_implementation_drops_a_session_the_branch_undid` |
| Model/tool split of the time; shorter rows; a visible "click for details" on This guide | 20:11 | cost-v1 | 6cb61ff | `test_harness_cost.py::test_the_four_rows_carry_a_time_column_and_a_dash_when_untimed` *(edited)* |
| Column "COMPONENT" becomes "Step"; the model/tools line becomes the hover of the time | 20:39–20:40 | cost-v1 | 6cb61ff | `test_harness_cost.py::test_the_four_rows_explain_only_the_prices_on_screen` *(edited)* |

## Footer / cross-cutting

| Change (Victor's ask) | Time asked | live-patch id(s) | Commit(s) | Verified by |
|---|---|---|---|---|
| Footer: drop the redundant "in your project" | 13:45 | — (text) | c79e999 | `test_build_review.py::test_the_footer_says_where_the_page_came_from_and_where_to_see_it` *(edited)* |
| ⇄ before "Single page" | 13:52 | — (text) | 4487b13 | `test_build_review.py::test_the_show_all_button_says_what_it_does_next` *(edited)* |
| Tab-level pill reads "Prompt to get this page"; smaller areas keep "Prompt to get this" | 13:15 | — (text) | d239c89 | `test_adopt.py::test_tab_title_pills_say_page_and_smaller_areas_keep_the_short_label` |
| Prompt pill hover: the agentic.how "Enroll" shimmer, in purple | 15:28 | fancy | 5c901c0 | — |
| Adversarial UX review of every tab (asked "have you spawned one?"): opaque tooltips, one-width pills, gear wording, UNCHANGED beside the file name, Deployment red arrow detours | 15:22 | uxpolish, uxpolish-js | 36a0f70 | `test_ux_polish.py::test_10_tooltips_are_opaque`, `::test_5_the_extension_column_is_one_width`, `::test_8_unchanged_sits_beside_the_file_name` (d4fc02b); `test_action_server.py::test_the_masthead_gear_and_a_tab_gear_say_the_same_thing`; `test_drawio_diff.py::test_a_red_arrow_goes_round_a_box_instead_of_through_its_label` |
| Cursors: a hand on clickable things, "?" only on tooltip-only things | 15:21 | 1522, uxpolish | 9938bdd, 36a0f70 | `test_ux_polish.py::test_16_a_link_gets_the_hand_not_the_question_mark` |
| One disclosure caret everywhere (Complexity's 13px ▶/▼) | 20:27 | carets | e483e8d | — |
| Blue (i) "What am I looking at?" beside every prompt pill; fix the pill animation's black corner | 20:30, 20:41 | explain, explain-js | 8576b03 | `test_adopt.py::test_every_placed_pill_gets_an_i`, `::test_the_i_sits_right_after_the_pill_inside_its_row`, `::test_the_pill_burst_is_a_square_so_no_angle_leaves_a_corner_bare` (+6 more) |
| (i) texts rewritten the way Victor explained each tab in the talk, kept brief | 22:30, 22:58 | — | 32fc611 | `test_adopt.py::test_each_explainer_is_one_to_three_short_lines_and_names_a_real_piece` |

**Build plumbing only (no UI ask):** 080fa58, 9150b1e, 757a170, 4e20850, b2b7711, e3cc5e9 (re-exports and import fixes). 7770143 republishes the demo snapshot.

**In the build with no matching ask found:** 78cc0ba (Sequence: a card drawn from the committed .puml carries the committed sidecar; `test_build_review.py::test_a_card_drawn_from_the_committed_puml_carries_the_committed_sidecar`) and be362c0 (Complexity: each class in the call graph gets its own border colour; no test).

## Not ported / open

**Asks with no commit in the build:**
- ~~**API toggle label "expand 25 changes" (15:05).**~~ Was a hand text edit only; ported in **67825e7** during the rebuild check (below).
- **Drop the notification-service → commons Maven dependency on petclinic `main` (15:04).** The agent found that notification-service really does use commons (`VisitBookedNotification`, `PhoneNumbers`), so it changed nothing. The question of copying the classes or keeping the link is still open. This is not a report change.
- **Status-bar click should start serving the report (12:38).** This lives in the `victor-vsc` extension, outside these three repos. Not checked here.
- **Talk link previews on victorrentea.ro (15:42).** Another repo, deployed as 35cf192. Not a report change.
- **Tests-tab wire bend limit (21:08 exchange).** Hand-added to the PR #51 page only. The agent says the build already had it, so there is no commit and no live-patch id.

**Live-patch blocks with no matching commit:** none. Every block on both pages maps to a commit above. `live-patch-fixture-dots--` and `live-patch-dataset-view--` are only HTML comment markers. `live-patch-1249`, named in the session summary, is no longer in either page.

**Caveat on two rows:**
- `live-patch-1621` (sans-serif font for `.tip .tiplist li`) is matched to d0a08f1's `ul.tiplist.prose` rule; the rebuild check confirmed the hover tooltips get it.
- The 20:36 ask "double the space between the Cost title and its header" was sent to the cost agent. It presumably landed in 6cb61ff, but the commit body doesn't mention it.

## Rebuild check (night of 7→8 Oct)

Nobody had proven that a from-scratch build reproduces the hand-polished pages, so both were
regenerated by the program and compared, adversarially, against the final snapshot
(`human-review-backups/2026-10-07-live-polish/final-2142/`).

**How it was run**
- Round 1. `refresh-report.py --force --steps <every step but video>` on both checkouts,
  no model calls. The video was skipped on purpose: the film is data, today's patches never
  touched it, and re-filming deletes and re-buys the Fish narration voices. No Fish call was made.
  The paid pairing (`rerun-model.py`) was not run either.
- Round 2. `--steps static --force` after the fixes.
- Round 3. A page-only rebuild after the last two fixes.
- Comparison. Headless Chromium at 1152×625, DPR 2, dark and light, on every tab, plus:
  - Tests chapters toggled, and All tests;
  - Demo 👁;
  - every (i) open;
  - New/Old and radius;
  - Cost details.
- Each shot has a pixel diff and a visible-text diff against the backup.
- A CSS probe re-injected each live-patch block into the regenerated page and compared
  computed styles with and without it.
- 4 Opus reviewers looked for differences (round 1), then 2 verified the fixes (round 2).

**Gaps found and fixed in the build** (each with a test):

| Gap the rebuild exposed | Commit | Test |
|---|---|---|
| API toggle said "expand N impacted" (hand edit never ported) | 67825e7 | `test_openapi_visual_diff.py::test_the_expand_toggle_counts_changes_by_that_name` |
| test-pr Cost billed the undone session again after main was merged ($11 → $27) | d342c6b | `test_harness_cost.py::test_the_reset_still_counts_after_main_is_merged_into_the_branch` |
| draw.io Deployment / Conceptual cards got the PlantUML prompt and (i) (head parsed up to the nested buttons) | 5005856 | `test_adopt.py::test_a_drawio_card_whose_head_holds_its_action_buttons_is_still_a_drawio_piece` |
| draw.io edit buttons lost "Open in the draw.io desktop app / on the web" (hand edit) | 1c0f00d | `test_diagram_views.py::test_both_editors_are_offered_and_named` |
| UX how-box air, solid underline when open; span carets not blue on hover; caret gap; Tests carets 12px/text-colour/.8; Tests row fan 1px off; Sequence caret 7–9px too far right; caret hover ease; caret selector lists styling a whole `<details>` | d5ac53a, 522dfb4 | `test_ds_audit.py::test_the_count_opens_a_box_that_names_each_side_once`, `test_ux_tab.py::test_a_span_caret_goes_link_blue_with_its_row_like_the_pseudo_ones`, `::test_the_caret_selector_lists_never_name_a_bare_details`, `test_ux_polish.py::test_12_tests_fan_and_caret_are_readable_on_dark` |
| test-pr API: "expand" opened 16 of 25 changes (array `Items` stuck since bodies open on Schema) | aabf249 | `test_openapi_visual_diff.py::test_a_node_that_will_not_open_gets_its_tree_redrawn_once` (+ in-browser: 25/25 on r2) |
| Title-row chips and score pill 2–3px wider a side; behind-main mark 600 not 700; Demo transcript touching its pill; container chips gap | 19233f2, 7a48c32 | `test_ux_polish.py::test_title_row_badges_keep_the_side_padding_tuned_live`, `::test_the_behind_main_mark_is_as_bold_as_the_ahead_one`, `::test_demo_transcript_pill_and_container_chips_keep_their_live_spacing` |
| API quiet controller drew a tinted band and a grey status caret Victor never saw (the patch's variable was undefined live) | 17a2762 | `test_openapi_visual_diff.py::test_a_quiet_controller_and_a_status_caret_look_as_they_did_live` |
| (stale, not a regression) three `test_harness_cost.py` assertions from before the 4 Oct Cost redesign | ad61838 | — |

Public copy of `openapi-visual-diff.py` synced in OpenAPI-Visual-Diff (fca66cd, 7935aaa, a9e06e1, e88d57b).

**Where the evidence is** (outside the repo, next to the backups):
`~/workspace/human-review-backups/2026-10-07-rebuild-check/`.
- `shots/bk-*` are the backups; `r1-*` is the first rebuild; `r3-*` is the final one. Each is a full page per tab and state, in `.png` and `.txt`.
- `cmp/r1-*` and `cmp/r3-*` are side-by-sides (backup | rebuild | diff mask), with text diffs and a `summary.txt`.
- `reviews/` holds the reviewers' findings and the per-patch inventory.
- `tools/` holds the scripts, which can be re-run.

**Result**
- PR #51 (96 patch blocks): 93 reproduced or obsolete with the same look; 3 partly, all decisions for Victor (below). 0 lost.
- PR #49 (24 blocks): all reproduced.

**Differences that are expected (data, not build):**
- Masthead drift: main was merged into both branches at 21:13, so `5↓main` and `+1` are gone on PR #51, and `7↑` became `8↑` on PR #49. Files, lines and tests counts moved with the new merge-base.
- The (i) texts were rewritten from the talk (32fc611).
- Tests: a "pairing predates the coverage run" band and new E2E counts (coverage re-run, paid pairing not).
- Re-captured pictures: sequence, C2, City, UX shots.
- The new Voices row on Cost (9704803).
- PR #49 Sequence: the first run's suite went red on a 60 s Before-hook timeout. That was environmental: a re-run was 7/7 green, with the same 5 diagrams. C2 now also projects the two VisitTest traces.

**Left for Victor to decide** (the build and the backups disagree, or the two backups disagree with each other):
- **PR #51 Review folds.** Margins, tinted summary, mono stat and a nested box. The generator's look equals the PR #49 backup, not the PR #51 hand patch.
- **PR #51 Deployment card.** It shows Diff/New/Old plus a ⇔ mark, because 3 traced Commons calls are missing from the drawing. The backup showed UNCHANGED, typed in by hand. As a result the Structure tab is no longer greyed out.
- **Tests "Issue #25".** Patch 1312 asked for link-blue, which the build now draws. Live it stayed grey, because a later rule won.
- **PR #51 open Sequence pair.** Patch 1437 padded the whole card. The build moves only the row, so the open diagram sits 7px further in.
- **City.** No caption under the shot names the colour metric.

<details><summary>Every live patch, one row each</summary>

| Patch | Report(s) | What it does | Reproduced by the build? | Evidence |
|---|---|---|---|---|
| `1312` | pc | `.rm-num` inherits link; dsa caret/count; seqlang absolute | yes (seqlang + caret colour obsolete) | #25 blue 700 (left for Victor); count dotted, offset 3px |
| `1318` | pc | draw.io strokes 2px, `dgm-edit` inline-flex | yes | probe 0 diffs |
| `1321` | pc | `dgm-edit` orange border/text, dark variant | yes | probe 0 diffs; crop dep-stack-dark.png |
| `1326` | pc | shield avatar 24px, svg 20px, `rm-st` −4px | yes | probe display/font-size differ on an svg-only box; rect identical |
| `1328` | pc | masthead padding-top 0, h1 lh, score pr, VSC 🔗 | yes; 🔗 part obsolete | diff=0; 🔗 replaced by vscplug 🔌 (commands.css) |
| `1334` | pc | (cx part) Complexity kind-cols grid, right-aligned headers | yes | probe 0 diffs (`.refchip .drift` is masthead) |
| `1338` | pc | thead padding-right 5px, run icon −4px | yes | probe same; rm-run 1092, rm-st 1111 both |
| `1339` | pc | thead centring, chev 12px, `.rm-link` −4px | yes (`.rm-catf` part obsolete) | probe 1 diff -> 0; pill 583.7 = head pill |
| `1340` | pc | howbox air, `<p>` headings, solid underline when open | yes (fixed in d5ac53a + 522dfb4) | box 216.4px tall on r3, as on the backup |
| `1348` | pc | `.rm-tw` margin/padding in thead | yes | probe same |
| `1350` | pc | empty score `<i>` hidden; score padding-right .5rem | yes | titlescore pad 0 8px 0 8.8px == bk; cssprobe diff=0 |
| `1351` | pc | E2E pill solid orange, both schemes | yes | #c2610f/#fff4e6 dark, #e8780f/#fff light on Tests and Sequence |
| `1422` | pc | title-row chips .55rem sides, font .8rem, rings 21px | yes | chip pad 8.8px, w 54.1/73.3 == bk; cssprobe diff=0 |
| `1424` | pc | titleside and chips inline-flex centred | yes | cssprobe same |
| `1425` | pc | hidden title-row chips display:none | yes | cssprobe same |
| `1432` | pc | rerun ring size; `.titlerow.oneline` align centre | yes (21px superseded by 1516's 18px) | served: rings 18x18 == bk |
| `1437` | pc | testpair card padding-left 8px | partly | shut row x 29 = bk; open exhibit x 36.2 vs 29 (keeps card padding) |
| `1440` | pc | 24px caret; pill min-width 4.5em; filter-pill padding | yes (pill 45px); caret size/.rm-catf obsolete | caret superseded by 1506 then carets 13px; `.rm-catf` absent in bk too |
| `1452` | pc | filemark colours edited/unchanged, svg 15px | yes | edited 224,163,60; unchanged 154,154,168; new = green (newer) |
| `1505` | pc | Demo transcript stretches; pill flex 0 0 auto, mt .4rem | yes | gap 6.4+7.2px, transcript 417.9 == bk; residual align-items diff no effect |
| `1506` | pc | muted caret, link on hover with .12s ease | yes | transition 0.12s color on r2-pc/vv; 19px size superseded by carets 13px |
| `1507` | pc | no underline on action buttons, brighter on hover | yes | probe 0 diffs |
| `1515` | pc | angry-bot icon size and offset | yes | misc: 14x13.8 va -1.968px == bk |
| `1516` | pc | title rerun rings 18px square | yes | served: 18x18 at same x; rr-ico display diff invisible |
| `1517` | pc | pods own line, `[hidden]`, gap .35rem, appenv margin | yes | pods gap 5.6/5.6 order 99 basis 100%; appenv y 88.4 |
| `1522` | pc | filter pills cursor pointer | obsolete | `.rm-catf` unmatched in bk too |
| `1531` | pc | `capped` without strike-through, cursor help | yes | gradewhy-was td=none cur=help (class renamed) |
| `1533` | pc | fold bar left-aligned path | yes (inside the fold restyle left to Victor) | cssprobe only text-align start→left |
| `1544` | pc | quiet tab no underline | yes (rule present); pc Structure not quiet (left for Victor) | frame.css:30; no `.tab.quiet` in r2 |
| `1549` | pc | `N↑` bold drift, cursor help | yes | r2-vv 8↑ fw=700 cur=help (gains 4.8px left, §2) |
| `1552` | pc | Tests grid 474fr/520fr, gap 20px | yes | 520.719px 571.281px, gap 20px |
| `1600` | pc | fold stat pushed right; snipfold figure border-top | partly; restyle left for Victor | stat right yes; fold look == vv backup, != pc hand patch |
| `1620` | pc | `+N` badge as bold text, no pill or caret | yes | masthead.css:131-136; injected badge fw=700 p=0 |
| `1621` | pc | tooltip list li sans, code mono | yes | tip.js `.tiplist.prose` (round 1 hover.py; tip code unchanged) |
| `1622` | pc | voice emoji 1.15em, label gap | yes | beh2: voice-switch 941.4,150.6 132x20 == bk |
| `1624` | pc | voice switch inline-flex pills, gap .7rem | yes | identical boxes; align-items diff invisible |
| `1626` | pc | voice switch in h2, top -3px, pl .9rem | yes (selector obsolete: `.vidhead`) | voice-switch box identical to bk |
| `api-polish.js` | pc, vv | info corner, compact params, 2xx-open folds, Schema default | yes (array walk fixed, band/caret as approved) | 25/25 hits; folds h=27; caret fg; quiet bg transparent |
| `apishadow.js` | pc | no controller spine; collapsed controllers and arrows grey | yes | api1: div border-left 0, h3 grey, arrow fill grey |
| `carets` | pc, vv | one 13px muted ▶/▼, link on hover, `.rm-chev` full strength | yes | probe 12/13 diffs (r1) -> 0; `.disclose` and `.cx-caret` hover link-blue |
| `carets (fold part)` | pc, vv | one ▶︎/▼︎ 13px muted caret, no marker | yes | cssprobe r2 carets: diff=0 (pc and vv) |
| `cm-actions` | pc, vv | `dgm-edit` pill look, buttons in the card head | yes | only `.badge + .rerun-acts` unmatched (pc Deployment card left for Victor) |
| `cost-v1` | pc, vv | cost table layout, sub-rows, details toggle | yes | sigc r2 vs bk: only the Voices row added |
| `cxcols` | pc, vv | added header green, total fg, `.cx-n` bold | yes | renamed `cx-colh-added/-total`; colours equal; probe unmatched = old names |
| `cxcols-js` | pc, vv | adds the header classes at runtime | obsolete | the generator emits `cx-colh-added/-total` server-side |
| `dataset-view (css + js)` | pc, vv | 👁 per fixture, tables under the band | yes | eye crops: vv pixel diff 0; pc only 0.2px shift |
| `dgm-morph` | pc, vv | radius morph animation, sticky chooser | yes | state-only classes present; probe unmatched = state-only, same in r1 |
| `docker-status (css + js)` | pc | per-container chips under Start App in Docker | yes | app-env.js appenvPods; pod CSS gap 5.6px |
| `drag` | pc | SQL panel draggable by its head | yes | drag +100,+50 moves the panel +100,+50 |
| `drag-css` | pc | SQL panel head cursor move | yes | cursor move on r2 |
| `drawio-morph` | pc, vv | Diff/New/Old swap morph CSS | yes | `dgm-m-glow-own` present; state-only |
| `drawio-morph (css + js)` | pc, vv | Diff/New-Old morph for draw.io | yes (newer build) | morph2: no anims either side; cssprobe unmatched (state-only) |
| `drawio-morph-js` | pc, vv | Diff/New/Old swap morph script | yes | generator JS present (round 1), unchanged by the fixes |
| `dsahow` | pc | count click/Enter toggles the box + aria-expanded | yes | click: hidden=false, aria=true on r2 |
| `explain` | pc, vv | blue (i) beside each prompt pill, explainer box | yes | Deployment box 832×86 at x 283 on bk and r2 |
| `explain (css + js)` | pc, vv | blue (i) and box beside each pill | yes | hrx-box identical style; vv draw.io pieces correct now |
| `explain-js` | pc, vv | per-piece explainer texts and toggling | yes | Deployment/Conceptual now draw.io texts (rewritten per 32fc611) |
| `fancy` | pc | shimmer on the Prompt pill | yes | cssprobe same (adopt.css) |
| `fixture-dots` | pc, vv | a dot per DB fixture on E2E rows | yes | same rows, tip "DB Fixture: Default · click to view the data" |
| `fixture-dots (css + js)` | pc, vv (Demo side) | coloured dot per DB fixture button | yes | dots 9.6px #8b929c/#2fa84f, same positions |
| `fixture-dots-css` | pc, vv | fixture dot style (ring, colour) on E2E rows | yes | 9.6px dot, ring box-shadow identical |
| `ghfold-css` | pc | fold look (margins, summary padding, border) | partly; left for Victor | sig: m 8→14.4px, summary tint, mono bar |
| `ghfold.js` | pc | fold each diff under its file bar | yes (static) | 42 `details.ghfold` |
| `iconalign` | pc, vv | (tabre part) rerun icon vertical-align middle, top −.11em | yes (tabre part) | probe: only the `#behaviour .voice-switch` rules differ (Demo, not mine) |
| `masthead-r4` | pc | strip padding for rings; title row pinned 18px | yes; strip rule obsolete (rings left the strip) | cssprobe r2 diff=0, 1 unmatched selector |
| `plus1.js` | pc | `+N` badge before head ref, margin 0 .1rem 0 .3rem | yes | masthead.py:247 `{ahead_mark}{badge}{ref}`; same inline values in CSS |
| `prpush-css` | pc | publish dialog styling | yes | pp-err/list/ok/q/sub/text/where in review.css |
| `prpush.js` | pc | `in VS Code` per finding; publish flow | yes (links now static) | 43 `a.f-vsc` with `vscode://file…`; push code in review.py |
| `review-sym (css + js)` | pc, vv | confidence chip colours; excerpt path left | yes | misc: sev-med/sev-info colours, mono 700 15px r5 |
| `seqfile` | pc | label .8rem, filemark 14px, dotted link | yes | underline-offset moot (decoration none); dotted border-bottom 1px same |
| `seqfile-js` | pc | clicking the file link doesn't toggle the fold | yes | drag.py: open stays False on r2 |
| `seqlang` | pc | file label absolutely positioned at the right edge | obsolete (replaced by seqlang-final) | file link right edge 1115.8 on bk and r2 |
| `seqlang-final` | pc | summary flex, label auto-margin right, 13px caret | yes | align-items baseline vs center, no visible effect; pill/link centres within 0.3px |
| `seqwhy` | pc | outline @/+/✍️ badges, muted small file label | yes | probe: only the sw-at font fallback list differs; tips identical |
| `snipfold.js` | pc | fold excerpts of 2+ lines | yes (static) | 9 `details.ghfold.snipfold` |
| `tabh` | pc, vv | tab height 19.75px | yes in effect | tab h=19.8 both; lh 18.6→22.576 only |
| `tabicons` | pc | rerun rings after each tab title | yes (renamed `.tabre`) | server-side `span.tabre`, hidden on a static copy |
| `tabicons (+ -js)` | pc | rerun rings beside Demo/API/Data/Review titles | yes (`.tabre-head` → `.tabre`) | tabre.js positions identical on all four pages |
| `tabicons-2` | pc | 18px rerun button inside `.tabre-head` | yes (renamed) | `commands.css` `.tabre` 18px |
| `tabicons-3` | pc | card-head `.tabre-head` font/colour | yes (renamed) | as round 1 |
| `tabicons-4` | pc | `.tabre-head` offsets in h2/card heads | yes (renamed) | as round 1 |
| `tabicons-4 (+ -js)` | pc | ring offsets; API ring moved to band end | yes (renamed) | pc API ring 534.8 == bk; vv at line end 606.5 |
| `tabicons-4-js` | pc | moves API verdict `.tabre` to the end | obsolete for my tabs (API) | not in my tabs |
| `tabicons-5` | pc | Tests h2 block + 76px for rerun icons | yes | as round 1; untouched by the fixes |
| `tabicons-6 (+ -js)` | pc | h2 + transcript into `.vidside` beside the video | yes | vidside 828,144 304x496.8 == bk |
| `tabicons-7` | pc | voice switch wrap/no-wrap in vidside h2 | yes (selectors obsolete, `.vidhead`) | identical px |
| `tabicons-js` | pc | injects `.tabre-head` rows at runtime | obsolete | the generator emits `.tabre` in every h2 |
| `tests-all` | pc, vv | dotted underline on the ext; preview hides srcbar | yes | dotted 3px offset; `.rm-srcbar` unmatched (state-only) |
| `tests-chapters` | pc, vv | three chapters by kind, chapter heads, covpop | yes | probe 6 diffs (r1) -> 0; chev 13px muted 1 |
| `tests-chapters-js` | pc, vv | chapter grouping, counts, shield popover | yes | popover 764,211, same lists |
| `tests-tab` | pc | one-window-tall `.rm-body`, cov-head flex | yes | docH 625, `--rm-tail-h` 82px |
| `tests-tab-js` | pc | ext-only label + path tip, `.cov-head` wrapper, fit() | yes | `.feature` label, tip `owner-search.feature:38 — Open in VS Code` |
| `tledger` | pc | ledger inline-flex gap | yes | probe 0 diffs |
| `uxpolish` | pc | #4 New/Old, #5 ext 51px, #6, #8, #12, #15, #16 | yes (#6, #12 obsolete) | #12 .8 overridden by carets in bk; r2 opacity 1 = bk look |
| `uxpolish-js.js` | pc | API shadow bar colours, hollow dot, 80px badges | yes | api1/api8: identical to bk-pc (vv inherits) |
| `uxpolish.css (masthead/Data/Demo items 4, 8, 10, 11, 16, 17c)` | pc | New/Old colour, badge beside file, opaque tip, chip line box | yes | cssprobe r2: no diffs; 2 unmatched (no badge / Tests) |
| `voicemove.js` | pc | move voice radios into the Intro video title row | yes (generator places them statically) | live/eye crops: radios in title row |
| `vscplug` | pc, vv | 🔌 on VSC-on | yes | served VSC-on w=68.77 == bk-pc |
| `widen` | pc, vv | wrap 1200px, masthead side padding, drifted border = line | yes | cssprobe same; masthead pad 0 20px |
| `hand edit "expand 9 changes"` | pc | toggle wording | yes | label `expand 9 changes` |
| `hand edit draw.io button tooltips` | pc | "Open in the draw.io desktop app / on the web" | yes | data-tip present on Data (vv) and Deployment (pc) |

</details>
