create table distance_summary as
    with dist as (
        select distinct
            distance
        from races_info
    ), horses as (
        select distinct
            horse_id
        from races
    ), dist_prep as (
        select
            distance
            , horse_id
        from dist
        join horses
            on True
    )

    select
        dp.horse_id
        , dp.distance
        , count(p.race_id) as n_races
    from dist_prep dp
    left join (
        select
            races_info.class
            , races_info.distance
            , races.horse_id
            , races.race_id
        from races_info
        join races
            on races_info.race_id = races.race_id
        ) p
        on dp.horse_id = p.horse_id
            and dp.distance = p.distance
    group by 1,2
;