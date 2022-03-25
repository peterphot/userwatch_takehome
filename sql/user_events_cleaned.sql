create schema if not exists detect;
drop table if exists detect.user_events_cleaned;
create table if not exists detect.user_events_cleaned as
    select
        source_ip
         , utc_time
         , utc_time + interval '1 minute'*(local_tz_offset*-1) as local_time
         , url
         , doc_path
         , case
               when event_type = 'pageview' and doc_path = '/' then 'view_index'
               when event_type = 'pageview' and doc_path <> '/' then 'view_'||replace(doc_path, '/', '')
               else event_type
        end as user_event
         , params_horse_id
         , params_country
         , params_race_class
         , params_distance
         , params_city
         , params_race_id
    from jitsu_events
    where True
      and not(url like '%http://127.0.0.1:5001/%')
;