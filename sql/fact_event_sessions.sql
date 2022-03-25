drop table if exists detect.fact_event_sessions;
create table if not exists detect.fact_event_sessions as
    with sessionisation_prep as (
        select
                extract(epoch from (utc_time - prev_utc_time))/60.0 as mins_between_events
             , case when extract(epoch from (utc_time - prev_utc_time))/60.0 >= 9.0 then 1 else 0 end as session_break
             , *
        from (
                 select
                     *
                      , lag(utc_time) over(partition by source_ip order by utc_time asc) as prev_utc_time
                 from detect.user_events_cleaned
             ) prep
    )


    select
        md5(source_ip||cast(sum(session_break) over(partition by source_ip order by utc_time asc) as text)) as session_id
         , source_ip
         , local_time
         , url
         , doc_path
         , user_event
         , params_horse_id
         , params_country
         , params_race_class
         , params_distance
         , params_city
         , params_race_id
    from sessionisation_prep
;