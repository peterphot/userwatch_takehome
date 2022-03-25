drop table if exists detect.vector_combinations;
create table if not exists detect.vector_combinations as
with vec_base as (
    select distinct
        s1.session_id as s1
                  , s2.session_id as s2
                  , s1.source_ip as ip1
                  , s2.source_ip as ip2
                  , v.doc_path
                  , v.user_event
    from detect.interaction_vectors v
             join (select distinct session_id, source_ip from detect.interaction_vectors) s1
                  on True
             join (select distinct session_id, source_ip from detect.interaction_vectors) s2
                  on True
    where True
      and s1.session_id <> s2.session_id
)

select
    vb.s1 as session_id_1
     , vb.s2 as session_id_2

     , vb.ip1
     , vb.ip2

     , vb.doc_path as doc_path
     , vb.user_event as user_event

     , coalesce(iv1.n, 0) as n_1
     , coalesce(iv2.n, 0) as n_2

     , coalesce(iv1.n_session_events, 0) as n_session_events_1
     , coalesce(iv2.n_session_events, 0) as n_session_events_2

     , coalesce(iv1.prop_interaction, 0) as prop_interaction_1
     , coalesce(iv2.prop_interaction, 0) as prop_interaction_2
from vec_base vb
         left join detect.interaction_vectors iv1
                   on vb.s1 = iv1.session_id
                       and vb.doc_path = iv1.doc_path
                       and vb.user_event = iv1.user_event
         left join detect.interaction_vectors iv2
                   on vb.s2 = iv2.session_id
                       and vb.doc_path = iv2.doc_path
                       and vb.user_event = iv2.user_event
;