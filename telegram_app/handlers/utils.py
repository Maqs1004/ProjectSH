import enum
from typing import NamedTuple


class ButtonInfo(NamedTuple):
    text: str | None = None
    callback: str | None = None


class Buttons:
    pay_by_telegram_stars = ButtonInfo(callback="pay_by_telegram_stars")
    back_button = ButtonInfo(text="back_button")
    resume_course = ButtonInfo(text="resume_course_button", callback="resume_course")
    restart_course = ButtonInfo(text="restart_course_button", callback="restart_course")
    pause_course = ButtonInfo(text="pause_course_button", callback="pause_course")
    show_user_course_info = ButtonInfo(callback="show_user_course_info")
    archived_courses = ButtonInfo(
        callback="archived_courses", text="archived_courses_button"
    )
    unfinished_courses = ButtonInfo(
        callback="unfinished_courses", text="unfinished_courses_button"
    )
    active_course = ButtonInfo(callback="active_course", text="active_course_button")
    sos = ButtonInfo(callback="sos", text="🆘")
    confirm_pay = ButtonInfo(callback="confirm_pay", text="confirm_pay_button")
    make_payment = ButtonInfo(callback="pay")
    course_payment_summary = ButtonInfo(text="course_payment_summary_button")
    resume_education = ButtonInfo(callback="resume_education")
    continue_button: ButtonInfo = ButtonInfo(text="continue_button")
    check_payment: ButtonInfo = ButtonInfo(callback="check_payment")
    telegram_stars: ButtonInfo = ButtonInfo(callback="telegram_stars")
    promo_code: ButtonInfo = ButtonInfo(text="promo_code_button", callback="promo_code")
    full_pay: ButtonInfo = ButtonInfo(text="pay_button", callback="full_pay")
    start_new_education: ButtonInfo = ButtonInfo(
        text="start_new_education_button", callback="start_new_education"
    )
    create_plan: ButtonInfo = ButtonInfo(
        text="create_plan_button", callback="create_plan"
    )
    preparing_questions: ButtonInfo = ButtonInfo(
        text="preparing_questions_button", callback="preparing_questions"
    )
    start_education: ButtonInfo = ButtonInfo(
        text="start_education_button", callback="start_education"
    )
    prepare_material: ButtonInfo = ButtonInfo(
        text="prepare_material_button", callback="prepare_material"
    )
    repeat_button: ButtonInfo = ButtonInfo(text="repeat_button")
    skip_button: ButtonInfo = ButtonInfo(text="⏩")
    ask_question: ButtonInfo = ButtonInfo(text="📝", callback="ask_question")
    next_stage: ButtonInfo = ButtonInfo(text="⏭", callback="next_stage")
    rating_up: ButtonInfo = ButtonInfo(text="👍🏽", callback="rating_up")
    rating_down: ButtonInfo = ButtonInfo(text="👎🏽", callback="rating_down")
    answer_question: ButtonInfo = ButtonInfo(callback="answer_question")


class Commands(enum.Enum):
    start: str = "start"
    balance: str = "balance"
    my_courses: str = "my_courses"
    help: str = "help"


class TranslationKeys:
    promo_code_applied_message: str = "promo_code_applied_message"
    answer_verification_error_message: str = "answer_verification_error_message"
    ask_questions_message: str = "ask_questions_message"
    available_courses_message: str = "available_courses_message"
    check_course_name_message: str = "check_course_name_message"
    checking_answer_message: str = "checking_answer_message"
    checking_prepare_answers_message: str = "checking_prepare_answers_message"
    confirm_payment_message: str = "confirm_payment_message"
    contact_support_message: str = "contact_support_message"
    correct_answer_message: str = "correct_answer_message"
    course_completion_message: str = "course_completion_message"
    course_pause_message: str = "course_pause_message"
    course_resume_message: str = "course_resume_message"
    course_restart_message: str = "course_resumed_message"
    creating_plan_message: str = "creating_plan_message"
    enter_promo_code_message: str = "enter_promo_code_message"
    help_message: str = "help_message"
    inactive_course_message: str = "inactive_course_message"
    incorrect_answer_message: str = "incorrect_answer_message"
    input_title_course_message: str = "input_title_course_message"
    insufficient_funds_message: str = "insufficient_funds_message"
    invalid_option_message: str = "invalid_option_message"
    limit_reached_message: str = "limit_reached_message"
    manage_courses_message: str = "manage_courses_message"
    material_prepared_message: str = "material_prepared_message"
    material_preparation_error_message: str = "material_preparation_error_message"
    material_ready_message: str = "material_ready_message"
    no_courses_start_message: str = "no_courses_start_message"
    not_generated_course_message: str = "not_generated_course_message"
    option_unavailable_message: str = "option_unavailable_message"
    payment_failure_message: str = "payment_failure_message"
    payment_options_message: str = "payment_options_message"
    payment_success_message: str = "payment_success_message"
    preparing_material_message: str = "preparing_material_message"
    preparing_questions_message: str = "preparing_questions_message"
    promo_code_discount_message: str = "promo_code_discount_message"
    promo_code_not_found_message: str = "promo_code_not_found_message"
    promo_code_reuse_message: str = "promo_code_reuse_message"
    questions_ready_message: str = "questions_ready_message"
    select_course_message: str = "select_course_message"
    start_later_button: str = "start_later_button"
    start_training_message: str = "start_training_message"
    support_message: str = "support_message"
    time_expired_message: str = "time_expired_message"
    topic_eligible_message: str = "topic_eligible_message"
    topic_forbidden_message: str = "topic_forbidden_message"
    toxic_warning_message: str = "toxic_warning_message"
    unfinished_course_message: str = "unfinished_course_message"
    validation_failure_message: str = "validation_failure_message"
    welcome_message: str = "welcome_message"
    your_training_plan_message: str = "your_training_plan_message"
