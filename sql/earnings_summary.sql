create table earnings_summary as

    select
        r.horse_id
        , sum(case
            when r.place = 1 then ri.prize_pool_first
            when r.place = 2 then ri.prize_pool_second
            when r.place = 3 then ri.prize_pool_third
            else 0
            end) as earnings
        , sum(fee) as entry_fees
    from races_info ri
    join races r
        on ri.race_id = r.race_id
    group by 1
;