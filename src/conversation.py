import re

from preferences import extract_preferences


class ConversationState:

    def __init__(self):
        self.preferences = None
        self.messages = []
        self.pending_preference = None
        self.latency_addressed = False

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def initialize(self, text):
        self.preferences = extract_preferences(text)

        self.messages.append({
            "role": "user",
            "content": text
        })

        return self.preferences

    # =========================================================
    # PENDING PREFERENCE
    # =========================================================

    def set_pending_preference(self, pref_name):
        self.pending_preference = pref_name

    def clear_pending_preference(self):
        self.pending_preference = None

    # =========================================================
    # MESSAGES
    # =========================================================

    def add_assistant_message(self, text):
        self.messages.append({
            "role": "assistant",
            "content": text
        })

    # =========================================================
    # NUMBER EXTRACTION
    # =========================================================

    def _extract_number(self, text):
        """
        Extract the first useful number from a user response.

        Examples:
            1500
            ₹1500
            40 hours
            30+ hrs
        """

        numbers = re.findall(
            r"\d+(?:\.\d+)?",
            text
        )

        if not numbers:
            return None

        return float(numbers[0])

    # =========================================================
    # AFFIRMATIVE / NEGATIVE
    # =========================================================

    def _is_affirmative(self, text):
        text = text.lower().strip()

        affirmative_phrases = [
            "yes",
            "yeah",
            "yep",
            "yup",
            "sure",
            "definitely",
            "absolutely",
            "of course",
            "correct",
            "right",
            "that's right",
            "that is right",
            "important",
            "very important",
            "i do",
            "i am",
            "i want that",
            "please do",
            "go ahead",
            "yes please"
        ]

        if text in affirmative_phrases:
            return True

        return any(
            text.startswith(phrase + " ")
            for phrase in affirmative_phrases
        )

    def _is_negative(self, text):
        text = text.lower().strip()

        negative_phrases = [
            "no",
            "nope",
            "nah",
            "not really",
            "not important",
            "don't care",
            "dont care",
            "not necessary",
            "unimportant",
            "i don't",
            "i dont",
            "no need"
        ]

        if text in negative_phrases:
            return True

        return any(
            text.startswith(phrase + " ")
            for phrase in negative_phrases
        )

    # =========================================================
    # RELATIVE VALUE UPDATES
    # =========================================================

    def _get_relative_change(self, text):
        """
        Detect relative changes such as:

            increase by 250
            increase it by 250
            raise the budget by 500
            add 200 to my budget
            decrease by 300
            reduce it by 100

        Returns:
            ("increase", value)
            ("decrease", value)
            None
        """

        text_lower = text.lower().strip()

        number = self._extract_number(text_lower)

        if number is None:
            return None

        increase_patterns = [
            r"\bincrease\b.*\bby\b",
            r"\bincreased\b.*\bby\b",
            r"\braise\b.*\bby\b",
            r"\braised\b.*\bby\b",
            r"\badd\b.*\bto\b",
            r"\badd\b.*\bmy\b",
            r"\bmore\b.*\bbudget\b",
            r"\badd\b.*\bmore\b"
        ]

        decrease_patterns = [
            r"\bdecrease\b.*\bby\b",
            r"\bdecreased\b.*\bby\b",
            r"\breduce\b.*\bby\b",
            r"\breduced\b.*\bby\b",
            r"\blower\b.*\bby\b",
            r"\bcut\b.*\bby\b",
            r"\bsubtract\b.*\bfrom\b"
        ]

        for pattern in increase_patterns:
            if re.search(pattern, text_lower):
                return "increase", number

        for pattern in decrease_patterns:
            if re.search(pattern, text_lower):
                return "decrease", number

        return None

    # =========================================================
    # BUDGET UPDATE
    # =========================================================

    def _update_budget_from_text(self, text):
        """
        Update budget intelligently.

        Examples:

            "increase the budget by 250"
                ₹1500 -> ₹1750

            "reduce my budget by 200"
                ₹2000 -> ₹1800

            "make the budget 2500"
                -> ₹2500

            "under 3000"
                -> ₹3000
        """

        if self.preferences is None:
            return False

        text_lower = text.lower().strip()

        # -----------------------------------------------------
        # Only handle this if the message is talking about
        # budget / price / spending.
        # -----------------------------------------------------

        budget_words = [
            "budget",
            "price",
            "spend",
            "spending",
            "cost"
        ]

        if not any(word in text_lower for word in budget_words):
            return False

        number = self._extract_number(text)

        if number is None:
            return False

        # -----------------------------------------------------
        # Relative change
        # -----------------------------------------------------

        relative_change = self._get_relative_change(text)

        if relative_change:
            operation, amount = relative_change

            current_budget = self.preferences.budget

            if current_budget is None:
                # If there is no existing budget, we cannot
                # meaningfully apply a relative change.
                return False

            if operation == "increase":
                self.preferences.budget = (
                    current_budget + amount
                )

            elif operation == "decrease":
                self.preferences.budget = max(
                    0,
                    current_budget - amount
                )

            return True

        # -----------------------------------------------------
        # Absolute budget
        # -----------------------------------------------------

        self.preferences.budget = number

        return True

    # =========================================================
    # BATTERY UPDATE
    # =========================================================

    def _update_playtime_from_text(self, text):
        """
        Handle battery/playtime updates.

        Examples:

            "increase battery by 10"
            20 -> 30

            "make battery 40 hours"
            -> 40

            "I want at least 50 hours"
            -> 50
        """

        if self.preferences is None:
            return False

        text_lower = text.lower().strip()

        battery_words = [
            "battery",
            "playtime",
            "play time",
            "hours"
        ]

        if not any(word in text_lower for word in battery_words):
            return False

        number = self._extract_number(text)

        if number is None:
            return False

        relative_change = self._get_relative_change(text)

        if relative_change:
            operation, amount = relative_change

            current_playtime = self.preferences.min_playtime

            if current_playtime is None:
                return False

            if operation == "increase":
                self.preferences.min_playtime = (
                    current_playtime + amount
                )

            elif operation == "decrease":
                self.preferences.min_playtime = max(
                    0,
                    current_playtime - amount
                )

            return True

        self.preferences.min_playtime = number

        return True

    # =========================================================
    # HANDLE PENDING QUESTION
    # =========================================================

    def _handle_pending_preference(self, text):

        if not self.pending_preference:
            return False

        pref = self.pending_preference
        text_lower = text.lower().strip()

        # -----------------------------------------------------
        # BUDGET
        # -----------------------------------------------------

        if pref == "budget":

            if self._update_budget_from_text(text):
                self.clear_pending_preference()
                return True

            value = self._extract_number(text)

            if value is not None:
                self.preferences.budget = value
                self.clear_pending_preference()
                return True

            return False

        # -----------------------------------------------------
        # MINIMUM PLAYTIME
        # -----------------------------------------------------

        if pref == "min_playtime":

            if self._update_playtime_from_text(text):
                self.clear_pending_preference()
                return True

            value = self._extract_number(text)

            if value is not None:
                self.preferences.min_playtime = value
                self.clear_pending_preference()
                return True

            return False

        # -----------------------------------------------------
        # LATENCY
        # -----------------------------------------------------

        if pref == "latency":

            if self._is_affirmative(text_lower):

                priorities = list(
                    getattr(
                        self.preferences,
                        "priorities",
                        []
                    )
                )

                if "latency" not in priorities:
                    priorities.append("latency")

                self.preferences.priorities = priorities
                self.latency_addressed = True

                self.clear_pending_preference()

                return True

            if self._is_negative(text_lower):

                priorities = list(
                    getattr(
                        self.preferences,
                        "priorities",
                        []
                    )
                )

                if "latency" in priorities:
                    priorities.remove("latency")

                self.preferences.priorities = priorities
                self.latency_addressed = True

                self.clear_pending_preference()

                return True

            # Explicit positive responses

            latency_positive_terms = [
                "low latency",
                "low lag",
                "less lag",
                "minimum latency",
                "minimal latency",
                "latency is important",
                "latency matters",
                "i need low latency",
                "i want low latency"
            ]

            latency_negative_terms = [
                "latency doesn't matter",
                "latency doesnt matter",
                "latency is not important",
                "latency isn't important",
                "i don't care about latency",
                "i dont care about latency"
            ]

            if any(
                phrase in text_lower
                for phrase in latency_positive_terms
            ):

                priorities = list(
                    getattr(
                        self.preferences,
                        "priorities",
                        []
                    )
                )

                if "latency" not in priorities:
                    priorities.append("latency")

                self.preferences.priorities = priorities
                self.latency_addressed = True

                self.clear_pending_preference()

                return True

            if any(
                phrase in text_lower
                for phrase in latency_negative_terms
            ):

                priorities = list(
                    getattr(
                        self.preferences,
                        "priorities",
                        []
                    )
                )

                if "latency" in priorities:
                    priorities.remove("latency")

                self.preferences.priorities = priorities
                self.latency_addressed = True

                self.clear_pending_preference()

                return True

            return False

        return False

    # =========================================================
    # UPDATE CONVERSATION
    # =========================================================

    def update(self, text):

        text = text.strip()
        text_lower = text.lower()

        # -----------------------------------------------------
        # 1. Resolve pending question first
        # -----------------------------------------------------

        pending_was_resolved = False

        if self.pending_preference:
            pending_was_resolved = (
                self._handle_pending_preference(text)
            )

        # -----------------------------------------------------
        # 2. Extract normal preferences
        # -----------------------------------------------------

        new_preferences = extract_preferences(text)

        # -----------------------------------------------------
        # 3. Handle explicit / relative budget updates
        # -----------------------------------------------------

        budget_was_updated = self._update_budget_from_text(text)

        # If the budget was updated using our custom logic,
        # don't overwrite it with the raw extracted number.
        if (
            not budget_was_updated
            and new_preferences.budget is not None
        ):
            self.preferences.budget = (
                new_preferences.budget
            )

        # -----------------------------------------------------
        # 4. Handle explicit / relative playtime updates
        # -----------------------------------------------------

        playtime_was_updated = (
            self._update_playtime_from_text(text)
        )

        if (
            not playtime_was_updated
            and new_preferences.min_playtime is not None
        ):
            self.preferences.min_playtime = (
                new_preferences.min_playtime
            )

        # -----------------------------------------------------
        # 5. Merge other preferences
        # -----------------------------------------------------

        if new_preferences.gaming is not None:
            self.preferences.gaming = (
                new_preferences.gaming
            )

        if new_preferences.anc is not None:
            self.preferences.anc = (
                new_preferences.anc
            )

        if new_preferences.enc is not None:
            self.preferences.enc = (
                new_preferences.enc
            )

        if getattr(
            new_preferences,
            "connectivity",
            None
        ):
            self.preferences.connectivity = (
                new_preferences.connectivity
            )

        # -----------------------------------------------------
        # 6. Preserve priorities
        # -----------------------------------------------------

        priorities = list(
            getattr(
                self.preferences,
                "priorities",
                []
            )
        )

        # Add explicit priorities extracted from new message

        for priority in getattr(
            new_preferences,
            "priorities",
            []
        ):

            if priority not in priorities:
                priorities.append(priority)

        # -----------------------------------------------------
        # Battery / playtime priority
        # -----------------------------------------------------

        if (
            "battery" in text_lower
            or "playtime" in text_lower
        ):

            if (
                "more important" in text_lower
                or "higher priority" in text_lower
                or "most important" in text_lower
            ):

                if "playtime" in priorities:
                    priorities.remove("playtime")

                priorities.insert(0, "playtime")

        # -----------------------------------------------------
        # Gaming priority
        # -----------------------------------------------------

        if (
            "gaming" in text_lower
            and (
                "more important" in text_lower
                or "higher priority" in text_lower
                or "most important" in text_lower
            )
        ):

            if "gaming" in priorities:
                priorities.remove("gaming")

            priorities.insert(0, "gaming")

        # -----------------------------------------------------
        # Price priority
        # -----------------------------------------------------

        if (
            (
                new_preferences.budget is not None
                or budget_was_updated
            )
            and "price" not in priorities
        ):
            priorities.append("price")

        self.preferences.priorities = priorities

        # -----------------------------------------------------
        # 7. Store user message
        # -----------------------------------------------------

        self.messages.append({
            "role": "user",
            "content": text
        })

        return self.preferences