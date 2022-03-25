drop table if exists detect.interaction_vectors;
create table if not exists detect.interaction_vectors as
select
    session_id
     , source_ip
     , doc_path
     , user_event
     , n
     , sum(n) over(partition by session_id, source_ip) as n_session_events
     , n/sum(n) over(partition by session_id, source_ip) as prop_interaction
from (
         select
             session_id
              , source_ip
              , doc_path
              , user_event
              , count(*) as n
         from detect.fact_event_sessions
         group by 1,2,3,4
     ) p
where True
;