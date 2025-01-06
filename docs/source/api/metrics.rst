Metrics
=======

Metric
---------------
.. automodule:: mixedvoices.metrics.metric
   :members:
   :undoc-members:
   :show-inheritance:

Default Metrics
---------------
The following metrics are provided by default:

.. py:data:: empathy
   :type: Metric
   
   Evaluates the bot's empathetic responses on a 0-10 scale.
   The bot should acknowledge what the user said and empathize by relating to their concerns

.. py:data:: verbatim_repetition
   :type: Metric
   
   Checks if the bot repeats itself word-for-word (PASS/FAIL).
   Similar but non-identical answers are acceptable.

.. py:data:: conciseness
   :type: Metric
   
   Measures response length and clarity on a 0-10 scale.
   Responses should be under 50 words while maintaining completeness.

.. py:data:: hallucination
   :type: Metric
   
   Detects if the bot makes claims not supported by its prompt (PASS/FAIL).
   Includes prompt content in evaluation.

.. py:data:: context_awareness
   :type: Metric
   
   Evaluates if the bot maintains conversation context (PASS/FAIL).
   Should acknowledge and incorporate user's previous statements.

.. py:data:: scheduling
   :type: Metric
   
   Rates appointment scheduling effectiveness on a 0-10 scale.
   Checks for gathering info, time/date handling, and confirmation.

.. py:data:: adaptive_qa
   :type: Metric
   
   Scores the bot's question relevance on a 0-10 scale.
   Questions should be topical and avoid repeating answered items.

.. py:data:: objection_handling
   :type: Metric
   
   Rates how well the bot handles objections on a 0-10 scale.
   Should acknowledge, empathize, and provide relevant solutions.

Helper Functions
----------------
.. autofunction:: mixedvoices.metrics.definitions.get_all_default_metrics