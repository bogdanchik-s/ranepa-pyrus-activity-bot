CREATE TYPE pyrus_approval_choice as ENUM('approved', 'rejected', 'acknowledged', 'revoked', 'waiting');
CREATE TYPE pyrus_task_action AS ENUM ('finished', 'reopened');

create table pyrus_task_event (
    id serial primary key,
    datetime timestamptz not null default CURRENT_TIMESTAMP,
    task_id bigint not null,
    task_form varchar(255),
    person varchar(255) not null,
    person_role varchar(255)[],
    person_approval_choice pyrus_approval_choice,
    comment_id bigint,
    comment_text text,
    approvals_added varchar(255)[],
    approvals_removed varchar(255)[],
    approvals_rerequested varchar(255)[],
    subscribers_added varchar(255)[],
    subscribers_removed varchar(255)[],
    subscribers_rerequested varchar(255)[],
    field_updates varchar(255)[],
    action pyrus_task_action
);
