create table class_summary as
with class as (
    select distinct
        class
    from races_info
), horses as (
    select distinct
        horse_id
    from races
), class_prep as (
    select
        class
         , horse_id
    from class
     join horses
          on True
)

select
    cp.horse_id
     , cp.class
     , count(p.race_id) as n_races
from class_prep cp
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
                   on cp.horse_id = p.horse_id
                       and cp.class = p.class
group by 1,2
;